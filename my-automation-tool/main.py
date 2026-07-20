"""MyAutoPlayer 程序入口：阶段 3 的单 Python 键盘测试宏。"""
from __future__ import annotations

import atexit
import ctypes
import sys
import threading
import time
from pathlib import Path

_IMPORT_STARTED_AT = time.perf_counter()

import keyboard
from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.hotkey_manager import HotkeyManager, TriggerMode
from src.core.global_hotkey import (
    DEFAULT_GLOBAL_HOTKEY,
    GlobalHotkeyError,
    load_global_hotkey,
    save_global_hotkey,
)
from src.core.sequence_player import SequencePlayer
from src.core.script_engine import (
    PythonMacro,
    PythonMacroRuntime,
    PythonMacroValidationError,
    load_python_macro,
    run_python_macro_once,
)
from src.core.macro_library import MacroEntry, MacroMetadata
from src.core.macro_file_manager import MacroFileError
from src.core.quick_click import (
    QuickClickController,
    QuickClickSettings,
    QuickClickSettingsStore,
)
from src.ui.macro_library_panel import MacroLibraryPanel
from src.ui.appearance import (
    AppearanceSettings,
    AppearanceSettingsStore,
    CLASSIC_LAYOUT,
    CLASSIC_THEME,
    GALLERY_LAYOUT,
    LAYOUT_OPTIONS,
    SAKURA_THEME,
    THEME_OPTIONS,
    stylesheet_for,
)
from src.ui.game_keybinds_panel import GameKeybindsPanel
from src.ui.osd_window import OsdPopup
from src.ui.window_chrome import (
    VerticalResizeHandle,
    WindowResizeHandle,
    WindowChromeController,
    WindowTitleBar,
    application_icon,
)
from src.ui.trigger_key_edit import TriggerKeyEdit, display_hotkey
from src.ui.rose_spin_box import RoseDoubleSpinBox, RoseSpinBox
from src.ui.sound_effects import SoundEffects
from src.ui.table_selection import PreserveForegroundSelectionDelegate
from src.utils.app_paths import macro_root, resource_root
from src.utils.logger import get_logger, setup_logging
from src.utils.single_instance import SingleInstanceGuard, show_already_running_message

logger = get_logger(__name__)
_MACRO_ROOT = macro_root()
_APP_TITLE = "自动连招"
_WINDOWS_APP_ID = "ssc8537.MyAutoPlayer"
_QUICK_CLICK_BINDING_ID = "__quick_click__"
_INSTRUCTION_TEXT = (
    "自动连招已启动\n\n按上方全局开关启用/禁用热键\n"
    "先在宏库启用一个 Python 宏，再按触发页设置的按键运行\n"
    "（鼠标不要在程序窗口内）"
)


def global_status_notification(disabled: bool) -> tuple[str, bool]:
    """返回全局开关 OSD 的文本和颜色状态。"""
    if disabled:
        return "全局脚本已禁用", False
    return "全局脚本已就绪", True


def _enable_per_monitor_v2_dpi() -> None:
    """必须在创建任何 Qt 窗口前调用，避免 Windows 位图放大造成模糊。"""
    if sys.platform != "win32":
        return
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        context = ctypes.c_void_p(-4)
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(context):
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass


class _HotkeyDispatcher(QObject):
    """在 Qt 主线程协调热键、OSD 和后台序列播放器。"""

    f9_stop_signal = Signal(str, int)
    macro_start_signal = Signal(object, str, int)
    toggle_signal = Signal(bool)
    player_finished_signal = Signal(str, int)

    macro_error_signal = Signal(str)

    def __init__(
        self,
        status_label: QLabel,
        osd_popup: OsdPopup,
        macro_runtime: PythonMacroRuntime,
        sound_effects: SoundEffects | None = None,
    ):
        super().__init__()
        self._status_label = status_label
        self._osd_popup = osd_popup
        self._macro_runtime = macro_runtime
        self._sound_effects = sound_effects
        self._players: dict[str, SequencePlayer] = {}
        self._player_generations: dict[str, int] = {}
        self._running_names: dict[str, str] = {}
        self._stop_lock = threading.RLock()
        self._pending_stop_generations: dict[str, int] = {}
        self._pending_starts: dict[str, tuple[PythonMacro, int]] = {}
        self._on_natural_finish = None
        self._on_binding_configuration = None
        self.f9_stop_signal.connect(self._stop_f9, Qt.ConnectionType.QueuedConnection)
        self.macro_start_signal.connect(self._start_macro, Qt.ConnectionType.QueuedConnection)
        self.toggle_signal.connect(self._apply_global_status, Qt.ConnectionType.QueuedConnection)
        self.player_finished_signal.connect(
            self._on_player_finished, Qt.ConnectionType.QueuedConnection
        )
        self.macro_error_signal.connect(
            self._show_macro_error, Qt.ConnectionType.QueuedConnection
        )

    def set_natural_finish_callback(self, callback) -> None:
        self._on_natural_finish = callback

    def set_binding_configuration_callback(self, callback) -> None:
        self._on_binding_configuration = callback

    def on_macro_hotkey(self, path: Path, binding_id: str, generation: int) -> None:
        """钩子线程只转发启动命令，绝不在物理 down/up 队列中读取或编译文件。"""
        self.macro_start_signal.emit(path, binding_id, generation)

    def on_macro_stop_hotkey(self, hotkey: str, generation: int) -> None:
        # 鼠标侧键的松开来自钩子线程；SequencePlayer.stop() 是线程安全的，
        # 直接请求停止可避免 Qt 队列繁忙时“松开后仍继续执行”。
        with self._stop_lock:
            self._pending_stop_generations[hotkey] = max(
                generation, self._pending_stop_generations.get(hotkey, -1)
            )
            pending = self._pending_starts.get(hotkey)
            if pending is not None and pending[1] <= generation:
                self._pending_starts.pop(hotkey, None)
            player = self._players.get(hotkey)
        if player is not None:
            player.stop()
        self.f9_stop_signal.emit(hotkey, generation)

    def on_toggle_hook(self, disabled: bool) -> None:
        """仅由 keyboard 钩子线程调用。"""
        self.toggle_signal.emit(disabled)

    def _on_player_finished_worker(self, binding_id: str, generation: int) -> None:
        """播放器线程仅转发信号，绝不直接触碰 Qt 控件。"""
        self.player_finished_signal.emit(binding_id, generation)

    @Slot(object, str, int)
    def _start_macro(
        self, macro_source: Path | PythonMacro, binding_id: str, generation: int
    ) -> None:
        with self._stop_lock:
            if self._pending_stop_generations.get(binding_id, -1) >= generation:
                if self._on_natural_finish is not None:
                    self._on_natural_finish(binding_id, generation)
                return
        if isinstance(macro_source, PythonMacro):
            macro = macro_source
        else:
            try:
                macro = load_python_macro(macro_source)
            except PythonMacroValidationError as exc:
                logger.warning("%s 未启动：%s", macro_source.stem, exc)
                if self._on_natural_finish is not None:
                    self._on_natural_finish(binding_id, generation)
                self.macro_error_signal.emit(f"{macro_source.stem} 宏无效，未启动")
                return
        # 文件读取/编译期间 release 仍可从钩子线程直接登记；播放前再检查一次。
        with self._stop_lock:
            stopped_at = self._pending_stop_generations.get(binding_id, -1)
            if stopped_at >= generation:
                if self._on_natural_finish is not None:
                    self._on_natural_finish(binding_id, generation)
                return
            if stopped_at >= 0:
                self._pending_stop_generations.pop(binding_id, None)
        player = self._players.get(binding_id)
        if player is None:
            player = SequencePlayer(
                on_finished=lambda run_generation: self._on_player_finished_worker(
                    binding_id, run_generation
                )
            )
            self._players[binding_id] = player
        elif player.is_running():
            with self._stop_lock:
                self._pending_starts[binding_id] = (macro, generation)
            return
        if not player.play(
            lambda stop_event: run_python_macro_once(macro, stop_event),
            macro.count,
            run_id=generation,
        ):
            with self._stop_lock:
                self._pending_starts[binding_id] = (macro, generation)
            return
        with self._stop_lock:
            self._player_generations[binding_id] = generation
            stop_was_requested = (
                self._pending_stop_generations.get(binding_id, -1) >= generation
            )
        if stop_was_requested:
            player.stop()
        self._running_names[binding_id] = macro.name
        logger.info("启动 Python 宏：%s，count=%s", macro.name, macro.count)
        self._osd_popup.show_notification(f"{macro.name} 宏运行中", success=True)

    @Slot(str, int)
    def _stop_f9(self, binding_id: str, generation: int) -> None:
        with self._stop_lock:
            self._pending_stop_generations[binding_id] = max(
                generation, self._pending_stop_generations.get(binding_id, -1)
            )
            pending = self._pending_starts.get(binding_id)
            if pending is not None and pending[1] <= generation:
                self._pending_starts.pop(binding_id, None)
            player = self._players.get(binding_id)
        if player is not None:
            player.stop()

    @Slot(str, int)
    def _on_player_finished(self, binding_id: str, generation: int) -> None:
        player = self._players.get(binding_id)
        if player is None:
            return
        current_generation = self._player_generations.get(binding_id)
        name = (
            self._running_names.pop(binding_id, "当前宏")
            if current_generation == generation
            else "当前宏"
        )
        logger.info("Python 宏自然结束：%s", name)
        if current_generation == generation:
            self._osd_popup.show_notification(f"{name} 宏已停止", success=False)
        if self._on_natural_finish is not None:
            self._on_natural_finish(binding_id, generation)
        with self._stop_lock:
            pending = self._pending_starts.pop(binding_id, None)
            stopped_at = self._pending_stop_generations.get(binding_id, -1)
        if pending is not None and stopped_at < pending[1]:
            self._start_macro(pending[0], binding_id, pending[1])

    @Slot(str)
    def _show_macro_error(self, message: str) -> None:
        self._osd_popup.show_notification(message, success=False)

    def stop_active_execution(self) -> None:
        with self._stop_lock:
            players = list(self._players.values())
        for player in players:
            player.stop()
        for player in players:
            player.join(timeout=2.0)

    @Slot(bool)
    def _apply_global_status(self, disabled: bool) -> None:
        notification, success = global_status_notification(disabled)
        if disabled:
            self._status_label.setText("● 热键已禁用")
            self._status_label.setStyleSheet("font-size: 20px; color: #8B6274; font-weight: 600;")
        else:
            self._status_label.setText("● 热键已启用")
            self._status_label.setStyleSheet("font-size: 20px; color: #6E4055; font-weight: 600;")
        self._osd_popup.show_notification(notification, success=success)
        sound_effects = getattr(self, "_sound_effects", None)
        if sound_effects is not None:
            (sound_effects.play_stopped if disabled else sound_effects.play_started)()


class MainWindow(QMainWindow):
    """阶段 3 运行入口和 v021 只读四页 UI 外壳。"""

    def __init__(self, macro_runtime: PythonMacroRuntime):
        super().__init__()
        self.setWindowTitle(_APP_TITLE)
        self._macro_runtime = macro_runtime
        self._hotkey_mgr: HotkeyManager | None = None
        self._macro_entries: list[MacroEntry] = []
        self._active_macro_path: Path | None = None
        self._registered_macro_hotkeys: set[str] = set()
        self._sound_effects = SoundEffects()
        self._osd_popup = OsdPopup(None)
        self._quick_click_store = QuickClickSettingsStore()
        self._quick_click_settings = self._quick_click_store.load()
        self._quick_click_controller = QuickClickController(
            on_finished=self._on_quick_click_finished
        )
        self._quick_click_controller.configure(self._quick_click_settings)
        self._appearance_store = AppearanceSettingsStore()
        self._appearance = self._appearance_store.load()
        self._focus_sound_played = False
        self._global_hotkey = self._load_global_hotkey()
        self._setup_ui()
        QApplication.instance().installEventFilter(self)
        self._dispatcher = _HotkeyDispatcher(
            self._status_label, self._osd_popup, macro_runtime, self._sound_effects
        )
        self._setup_hotkey()

    def _setup_ui(self) -> None:
        if not hasattr(self, "_macro_entries"):
            self._macro_entries = []
        if not hasattr(self, "_active_macro_path"):
            self._active_macro_path = None
        if not hasattr(self, "_global_hotkey"):
            self._global_hotkey = DEFAULT_GLOBAL_HOTKEY
        if not hasattr(self, "_quick_click_settings"):
            self._quick_click_settings = QuickClickSettings()
        if not hasattr(self, "_quick_click_store"):
            self._quick_click_store = QuickClickSettingsStore()
        if not hasattr(self, "_quick_click_controller"):
            self._quick_click_controller = QuickClickController()
            self._quick_click_controller.configure(self._quick_click_settings)
        if not hasattr(self, "_osd_popup"):
            self._osd_popup = OsdPopup(None)
        if not hasattr(self, "_appearance_store"):
            self._appearance_store = AppearanceSettingsStore()
        if not hasattr(self, "_appearance"):
            # 直接调用 _setup_ui 的离屏测试使用可靠的经典默认值。
            self._appearance = AppearanceSettings()
        self.setMinimumWidth(642)
        self.setWindowIcon(application_icon())
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setMinimumHeight(510)
        screen = QApplication.primaryScreen()
        if screen is not None:
            self.setMaximumHeight(screen.availableGeometry().height())
            self.setMaximumWidth(screen.availableGeometry().width())
        self.resize(642, 510)

        central_widget = QWidget()
        central_widget.setObjectName("app_surface")
        self.setCentralWidget(central_widget)
        resize_layout = QGridLayout(central_widget)
        resize_layout.setContentsMargins(0, 0, 0, 0)
        resize_layout.setSpacing(0)
        body = QWidget()
        body.setObjectName("window_body")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._resize_handles = {
            "top_left": WindowResizeHandle(
                self, Qt.Edge.TopEdge | Qt.Edge.LeftEdge, "window_resize_top_left"
            ),
            "top": WindowResizeHandle(self, Qt.Edge.TopEdge, "window_resize_top"),
            "top_right": WindowResizeHandle(
                self, Qt.Edge.TopEdge | Qt.Edge.RightEdge, "window_resize_top_right"
            ),
            "left": WindowResizeHandle(self, Qt.Edge.LeftEdge, "window_resize_left"),
            "right": WindowResizeHandle(self, Qt.Edge.RightEdge, "window_resize_right"),
            "bottom_left": WindowResizeHandle(
                self, Qt.Edge.BottomEdge | Qt.Edge.LeftEdge, "window_resize_bottom_left"
            ),
            "bottom": VerticalResizeHandle(self),
            "bottom_right": WindowResizeHandle(
                self, Qt.Edge.BottomEdge | Qt.Edge.RightEdge, "window_resize_bottom_right"
            ),
        }
        resize_layout.addWidget(self._resize_handles["top_left"], 0, 0)
        resize_layout.addWidget(self._resize_handles["top"], 0, 1)
        resize_layout.addWidget(self._resize_handles["top_right"], 0, 2)
        resize_layout.addWidget(self._resize_handles["left"], 1, 0)
        resize_layout.addWidget(body, 1, 1)
        resize_layout.addWidget(self._resize_handles["right"], 1, 2)
        resize_layout.addWidget(self._resize_handles["bottom_left"], 2, 0)
        resize_layout.addWidget(self._resize_handles["bottom"], 2, 1)
        resize_layout.addWidget(self._resize_handles["bottom_right"], 2, 2)
        resize_layout.setRowStretch(1, 1)
        resize_layout.setColumnStretch(1, 1)

        self._title_bar = WindowTitleBar(central_widget)
        self._window_chrome = WindowChromeController(self)
        layout.addWidget(self._title_bar)

        content_shell = QWidget()
        content_shell.setObjectName("content_shell")
        content_layout = QHBoxLayout(content_shell)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        side_panel = QWidget()
        side_panel.setObjectName("side_panel")
        side_panel.setFixedWidth(108)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(6, 8, 6, 8)
        side_layout.setSpacing(6)
        avatar = QLabel()
        avatar.setObjectName("gallery_avatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedHeight(72)
        avatar_pixmap = QPixmap(
            str(resource_root() / "assets" / "sakura-gallery-avatar.png")
        )
        if not avatar_pixmap.isNull():
            avatar.setPixmap(
                avatar_pixmap.scaled(
                    68,
                    68,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        side_layout.addWidget(avatar)
        gallery_title = QLabel("樱空画册")
        gallery_title.setObjectName("gallery_title")
        gallery_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(gallery_title)
        side_navigation = QListWidget()
        side_navigation.setObjectName("side_navigation")
        side_navigation.addItems(["宏库", "触发", "功能", "设置"])
        for index in range(side_navigation.count()):
            side_navigation.item(index).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        side_navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side_navigation.setCurrentRow(0)
        side_layout.addWidget(side_navigation, 1)
        side_panel.hide()
        content_layout.addWidget(side_panel)

        tabs = QTabWidget()
        tabs.setObjectName("main_tabs")
        tabs.setDocumentMode(True)
        tabs.setUsesScrollButtons(False)
        tabs.addTab(self._build_macro_page(), "宏库")
        tabs.addTab(self._build_trigger_page(), "触发")
        tabs.addTab(self._build_features_page(), "功能")
        tabs.addTab(self._build_settings_page(), "设置")
        content_layout.addWidget(tabs, 1)
        layout.addWidget(content_shell, 1)
        self._vertical_resize_handle = self._resize_handles["bottom"]
        self._tabs = tabs
        self._content_shell = content_shell
        self._content_layout = content_layout
        self._side_panel = side_panel
        self._side_navigation = side_navigation
        self._gallery_avatar = avatar
        side_navigation.currentRowChanged.connect(tabs.setCurrentIndex)
        tabs.currentChanged.connect(side_navigation.setCurrentRow)
        self._window_chrome.install(self._title_bar)
        self._on_macro_entries_changed(self._macro_panel.entries)
        self._apply_appearance(fit_layout=True)
        self._center_on_screen()

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        frame = self.frameGeometry()
        frame.moveCenter(screen.availableGeometry().center())
        self.move(frame.topLeft())

    @staticmethod
    def _select_combo_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _apply_appearance(
        self, *, persist: bool = False, fit_layout: bool = False
    ) -> None:
        """主题只改颜色，布局只改排版；两者可任意组合。"""
        self.setStyleSheet(stylesheet_for(self._appearance.theme))
        gallery = self._appearance.layout == GALLERY_LAYOUT
        self._side_panel.setVisible(gallery)
        self._tabs.tabBar().setVisible(not gallery)
        margins = (8, 8, 8, 8) if gallery else (0, 0, 0, 0)
        self._content_layout.setContentsMargins(*margins)
        self._content_layout.setSpacing(8 if gallery else 0)
        self.setMinimumWidth(760 if gallery else 642)
        if fit_layout:
            self.resize(840 if gallery else 642, self.height())
        if hasattr(self, "_trigger_detail"):
            self._trigger_detail.setFixedWidth(140 if gallery else 134)
        if hasattr(self, "_trigger_table"):
            widths = (40, 76, 68, 54) if gallery else (38, 70, 62, 44)
            for column, width in zip((0, 2, 3, 4), widths):
                self._trigger_table.setColumnWidth(column, width)
        if hasattr(self, "_theme_selector"):
            self._theme_selector.blockSignals(True)
            self._select_combo_data(self._theme_selector, self._appearance.theme)
            self._theme_selector.blockSignals(False)
        if hasattr(self, "_layout_selector"):
            self._layout_selector.blockSignals(True)
            self._select_combo_data(self._layout_selector, self._appearance.layout)
            self._layout_selector.blockSignals(False)
        self._update_appearance_description()
        if persist:
            try:
                self._appearance_store.save(self._appearance)
            except OSError as exc:
                logger.warning("外观设置保存失败：%s", exc)
            self._center_on_screen()

    def _update_appearance_description(self) -> None:
        if not hasattr(self, "_appearance_description"):
            return
        theme_text = (
            "樱花粉、天空蓝、薄荷绿和淡桃橙的轻盈卡片配色"
            if self._appearance.theme == SAKURA_THEME
            else "项目最初的 Candy 粉红配色"
        )
        layout_text = (
            "左侧导航、宽窗口与更充足留白"
            if self._appearance.layout == GALLERY_LAYOUT
            else "原始窄窗口与顶部四标签"
        )
        self._appearance_description.setText(
            f"当前：{theme_text}；{layout_text}。主题与布局可独立搭配。"
        )

    @Slot()
    def _on_appearance_changed(self) -> None:
        previous_layout = self._appearance.layout
        theme = self._theme_selector.currentData()
        layout = self._layout_selector.currentData()
        if not isinstance(theme, str) or not isinstance(layout, str):
            return
        self._appearance = AppearanceSettings(theme=theme, layout=layout)
        self._apply_appearance(
            persist=True, fit_layout=layout != previous_layout
        )

    @Slot()
    def _restore_classic_appearance(self) -> None:
        self._appearance = AppearanceSettings(
            theme=CLASSIC_THEME, layout=CLASSIC_LAYOUT
        )
        self._apply_appearance(persist=True, fit_layout=True)

    @staticmethod
    def _readonly_field(value: str) -> QLineEdit:
        field = QLineEdit(value)
        field.setReadOnly(True)
        field.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return field

    @staticmethod
    def _disabled_button(text: str) -> QPushButton:
        button = QPushButton(text)
        button.setEnabled(False)
        return button

    def _build_macro_page(self) -> QWidget:
        self._macro_panel = MacroLibraryPanel(_MACRO_ROOT, on_delete_requested=self._delete_macro)
        self._macro_panel.entries_changed.connect(self._on_macro_entries_changed)
        self._macro_panel.active_path_renamed.connect(self._on_active_macro_renamed)
        return self._macro_panel

    @Slot(object)
    def _on_macro_entries_changed(self, entries: list[MacroEntry]) -> None:
        self._macro_entries = list(entries)
        active_entry = self._entry_for_path(self._active_macro_path)
        if self._active_macro_path is not None and active_entry is None:
            self._active_macro_path = None
            self._macro_runtime.set_selected_path(None)
            if hasattr(self, "_dispatcher"):
                self._dispatcher.stop_active_execution()
            if self._hotkey_mgr is not None:
                self._hotkey_mgr.mark_finished("f9")
            logger.warning("活动宏已删除或失效，已安全停用")
        self._macro_panel.set_active_path(self._active_macro_path)
        self._render_trigger_rows()
        self._configure_independent_hotkeys()

    def _entry_for_path(self, path: Path | None) -> MacroEntry | None:
        if path is None:
            return None
        return next(
            (entry for entry in self._macro_entries if entry.valid and entry.path == path),
            None,
        )

    def _build_trigger_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        table = QTableWidget(0, 5)
        table.setObjectName("trigger_table")
        table.setHorizontalHeaderLabels(["序号", "名称", "按键", "模式", "状态"])
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setItemDelegate(PreserveForegroundSelectionDelegate(table))
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 名称列自动使用窗口增加的宽度，其余列保持紧凑并完整可见。
        table.setColumnWidth(0, 38)
        table.setColumnWidth(2, 70)
        table.setColumnWidth(3, 62)
        table.setColumnWidth(4, 44)
        header.setStretchLastSection(False)
        table.itemSelectionChanged.connect(self._show_selected_trigger_detail)
        table.cellClicked.connect(self._on_trigger_cell_clicked)
        self._trigger_table = table
        layout.addWidget(table, 1)

        detail = QGroupBox("触发详情（自动保存）")
        # 主窗口为固定宽度；固定右栏才能保证左侧四列表不会被内容建议尺寸挤压。
        detail.setFixedWidth(134)
        self._trigger_detail = detail
        form = QVBoxLayout(detail)
        form.setContentsMargins(7, 10, 7, 7)
        form.setSpacing(3)
        self._trigger_hotkey_field = TriggerKeyEdit()
        self._trigger_mode_field = QComboBox()
        self._trigger_mode_field.addItem("切换", "switch")
        self._trigger_mode_field.addItem("按下", "down")
        self._trigger_count_field = RoseSpinBox()
        self._trigger_count_field.setRange(0, 99)
        self._trigger_count_field.setSpecialValueText("持续")
        self._trigger_count_field.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self._trigger_speed_field = RoseDoubleSpinBox()
        self._trigger_speed_field.setRange(0.01, 8.0)
        self._trigger_speed_field.setSingleStep(0.1)
        self._trigger_speed_field.setDecimals(2)
        self._trigger_speed_field.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self._trigger_status_field = QComboBox()
        self._trigger_status_field.addItem("启用", True)
        self._trigger_status_field.addItem("禁用", False)
        for label, field in (
            ("热键", self._trigger_hotkey_field),
            ("模式", self._trigger_mode_field),
            ("次数", self._trigger_count_field),
            ("速度", self._trigger_speed_field),
            ("状态", self._trigger_status_field),
        ):
            form.addWidget(QLabel(label))
            form.addWidget(field)
        self._trigger_hotkey_field.hotkey_selected.connect(self._save_trigger_settings)
        self._trigger_mode_field.currentIndexChanged.connect(self._save_trigger_settings)
        self._trigger_count_field.valueChanged.connect(self._save_trigger_settings)
        self._trigger_speed_field.valueChanged.connect(self._save_trigger_settings)
        self._trigger_status_field.currentIndexChanged.connect(self._save_trigger_settings)
        layout.addWidget(detail)
        return page

    def _render_trigger_rows(self) -> None:
        selected_path = None
        rows = self._trigger_table.selectionModel().selectedRows()
        if rows and rows[0].row() < len(self._macro_entries):
            selected_path = self._macro_entries[rows[0].row()].path
        self._trigger_table.blockSignals(True)
        self._trigger_table.setRowCount(len(self._macro_entries))
        selected_row = None
        for row, entry in enumerate(self._macro_entries):
            if entry.valid:
                assert entry.macro is not None
                mode = "按下" if entry.macro.mode == "down" else "切换"
                values = (
                    str(row + 1),
                    entry.path.stem,
                    display_hotkey(entry.macro.hotkey),
                    mode,
                    "启用" if entry.macro.enabled else "禁用",
                )
            else:
                values = (str(row + 1), entry.path.stem, "—", "—", "错误")
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 1 and not entry.valid:
                    item.setForeground(Qt.GlobalColor.red)
                if column == 4:
                    if value == "启用":
                        item.setForeground(Qt.GlobalColor.green)
                    else:
                        item.setForeground(Qt.GlobalColor.red)
                self._trigger_table.setItem(row, column, item)
            if entry.path == self._active_macro_path or entry.path == selected_path:
                selected_row = row
        if selected_row is not None:
            self._trigger_table.selectRow(selected_row)
        else:
            self._trigger_table.clearSelection()
        self._trigger_table.blockSignals(False)
        self._reset_trigger_horizontal_scroll()
        self._show_selected_trigger_detail()

    @Slot()
    def _show_selected_trigger_detail(self) -> None:
        self._reset_trigger_horizontal_scroll()
        rows = self._trigger_table.selectionModel().selectedRows()
        entry = self._macro_entries[rows[0].row()] if rows else None
        if entry is None or not entry.valid:
            self._set_trigger_fields_enabled(False)
            return
        else:
            assert entry.macro is not None
            self._set_trigger_fields_enabled(True)
            # 回填被点击行的详情时不能伪装成用户录入热键；否则状态列第一下
            # 点击会先选中行，再把刚切换的状态保存回旧值。
            for field in (
                self._trigger_hotkey_field,
                self._trigger_mode_field,
                self._trigger_count_field,
                self._trigger_speed_field,
                self._trigger_status_field,
            ):
                field.blockSignals(True)
            self._trigger_hotkey_field.set_hotkey(entry.macro.hotkey)
            self._trigger_mode_field.setCurrentIndex(1 if entry.macro.mode == "down" else 0)
            self._trigger_count_field.setValue(entry.macro.count)
            self._trigger_speed_field.setValue(entry.macro.speed)
            self._trigger_status_field.setCurrentIndex(0 if entry.macro.enabled else 1)
            for field in (
                self._trigger_hotkey_field,
                self._trigger_mode_field,
                self._trigger_count_field,
                self._trigger_speed_field,
                self._trigger_status_field,
            ):
                field.blockSignals(False)

    @Slot(int, int)
    def _on_trigger_cell_clicked(self, row: int, column: int) -> None:
        self._reset_trigger_horizontal_scroll()
        if column != 4:
            return
        entry = self._macro_entries[row]
        if not entry.valid or entry.macro is None:
            return
        try:
            # 不依赖当前选中行：源码同样允许直接点击任意行的状态开关。
            self._macro_panel.update_trigger_settings(
                entry.path,
                hotkey=entry.macro.hotkey,
                mode=entry.macro.mode,
                count=entry.macro.count,
                speed=entry.macro.speed,
                enabled=not entry.macro.enabled,
            )
        except MacroFileError as exc:
            QMessageBox.warning(self, "保存触发设置失败", str(exc))

    def _set_trigger_fields_enabled(self, enabled: bool) -> None:
        for field in (self._trigger_hotkey_field, self._trigger_mode_field, self._trigger_count_field, self._trigger_speed_field, self._trigger_status_field):
            field.setEnabled(enabled)

    @Slot()
    def _save_trigger_settings(self, *_unused) -> None:
        rows = self._trigger_table.selectionModel().selectedRows()
        if not rows:
            return
        entry = self._macro_entries[rows[0].row()]
        if not entry.valid:
            return
        hotkey = self._trigger_hotkey_from_display()
        if hotkey == self._global_hotkey:
            self._trigger_hotkey_field.set_hotkey(entry.macro.hotkey)
            QMessageBox.warning(self, "保存触发设置失败", "该按键已是全局启停键，请换一个键。")
            return
        try:
            self._macro_panel.update_trigger_settings(
                entry.path,
                hotkey=hotkey,
                mode=self._trigger_mode_field.currentData(),
                count=self._trigger_count_field.value(),
                speed=self._trigger_speed_field.value(),
                enabled=bool(self._trigger_status_field.currentData()),
            )
        except MacroFileError as exc:
            QMessageBox.warning(self, "保存触发设置失败", str(exc))

    def _load_global_hotkey(self) -> str:
        try:
            return load_global_hotkey()
        except GlobalHotkeyError as exc:
            logger.warning("全局键设置无效，暂用默认反引号：%s", exc)
            return DEFAULT_GLOBAL_HOTKEY

    @Slot(str)
    def _save_global_hotkey(self, hotkey: str) -> None:
        if (
            getattr(self, "_quick_click_settings", QuickClickSettings()).enabled
            and self._quick_click_settings.hotkey == hotkey
        ):
            self._global_hotkey_field.set_hotkey(self._global_hotkey)
            QMessageBox.warning(
                self, "全局键未保存", "快捷连点正在使用这个按键，请先为快捷连点换键。"
            )
            return
        conflicting = next(
            (
                entry for entry in self._macro_entries
                if entry.valid and entry.macro is not None and entry.macro.hotkey == hotkey
            ),
            None,
        )
        if conflicting is not None:
            self._global_hotkey_field.set_hotkey(self._global_hotkey)
            QMessageBox.warning(
                self,
                "全局键未保存",
                f"“{conflicting.path.stem}”已使用这个触发键，请先为它换键。",
            )
            return
        try:
            saved = save_global_hotkey(hotkey)
        except GlobalHotkeyError as exc:
            self._global_hotkey_field.set_hotkey(self._global_hotkey)
            QMessageBox.warning(self, "全局键未保存", str(exc))
            return
        self._global_hotkey = saved
        manager = getattr(self, "_hotkey_mgr", None)
        if manager is not None:
            manager.set_global_disable_key(saved)
        self._global_hotkey_field.set_hotkey(saved)

    @Slot()
    def _save_quick_click_settings(self, *_unused) -> None:
        hotkey = self._quick_click_hotkey.hotkey()
        if hotkey == self._global_hotkey:
            self._quick_click_hotkey.set_hotkey(self._quick_click_settings.hotkey)
            QMessageBox.warning(
                self, "快捷连点未保存", "该按键已是全局启停键，请换一个键。"
            )
            return
        settings = QuickClickSettings(
            enabled=self._quick_click_enabled.isChecked(),
            hotkey=hotkey,
            mode=self._quick_click_mode.currentData(),
            interval_ms=self._quick_click_interval.value(),
        )
        try:
            saved = self._quick_click_store.save(settings)
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.warning(self, "快捷连点未保存", str(exc))
            return
        self._quick_click_settings = saved
        self._quick_click_controller.configure(saved)
        self._configure_quick_click_hotkey()

    def _configure_quick_click_hotkey(self) -> None:
        manager = getattr(self, "_hotkey_mgr", None)
        if manager is None:
            return
        manager.unregister(_QUICK_CLICK_BINDING_ID)
        settings = self._quick_click_settings
        if not settings.enabled or settings.hotkey == self._global_hotkey:
            return
        manager.register(
            settings.hotkey,
            self._quick_click_controller.start,
            mode=TriggerMode.DOWN if settings.mode == "down" else TriggerMode.SWITCH,
            stop_callback=self._quick_click_controller.stop,
            stop_on_release=settings.mode == "down",
            binding_id=_QUICK_CLICK_BINDING_ID,
        )

    def _on_quick_click_finished(self, generation: int) -> None:
        manager = getattr(self, "_hotkey_mgr", None)
        if manager is not None:
            manager.mark_finished(_QUICK_CLICK_BINDING_ID, generation)

    def _trigger_hotkey_from_display(self) -> str:
        return self._trigger_hotkey_field.hotkey()

    def _configure_independent_hotkeys(self) -> None:
        """刷新每个已启用宏的实时触发绑定；重复热键允许并发。"""
        manager = getattr(self, "_hotkey_mgr", None)
        if manager is None or not hasattr(self, "_dispatcher"):
            return
        desired: dict[str, tuple[Path, str, str]] = {}
        for entry in self._macro_entries:
            if not entry.valid or entry.macro is None or not entry.macro.enabled:
                continue
            hotkey = entry.macro.hotkey
            if hotkey == self._global_hotkey:
                logger.warning("跳过与全局键冲突的宏触发：%s", entry.path.name)
                continue
            binding_id = str(entry.path)
            desired[binding_id] = (entry.path, hotkey, entry.macro.mode)

        previous: dict[str, tuple[Path, str, str]] = getattr(
            self, "_registered_macro_configs", {}
        )
        if desired == previous:
            # 自己的原子保存还会触发 QFileSystemWatcher。相同快照只更新表格，
            # 绝不能再次重建绑定、清空 down/up 或让代次倒退。
            return

        for binding_id in set(previous) - set(desired):
            manager.unregister(binding_id)
        for binding_id, (path, hotkey, mode) in desired.items():
            if previous.get(binding_id) == (path, hotkey, mode):
                continue
            manager.register(
                hotkey,
                lambda generation, path=path, key=binding_id: self._dispatcher.on_macro_hotkey(
                    path, key, generation
                ),
                mode=TriggerMode[mode.upper()],
                stop_callback=lambda generation, key=binding_id: self._dispatcher.on_macro_stop_hotkey(
                    key, generation
                ),
                stop_on_release=mode == "down",
                binding_id=binding_id,
            )
        self._registered_macro_configs = desired
        self._registered_macro_hotkeys = set(desired)
        removed = manager.clear_pending_events()
        logger.info(
            "触发配置已即时生效：%s 个宏绑定，清理 %s 个旧边沿",
            len(self._registered_macro_hotkeys),
            removed,
        )

    def _reset_trigger_horizontal_scroll(self) -> None:
        """名称列始终可见；隐藏的横向滚动条不得保留偏移。"""
        bar = self._trigger_table.horizontalScrollBar()
        bar.setValue(bar.minimum())

    def _toggle_trigger_activity(self, row: int) -> None:
        entry = self._macro_entries[row]
        if not entry.valid:
            return
        if self._active_macro_path == entry.path:
            self._active_macro_path = None
            self._macro_runtime.set_selected_path(None)
        else:
            self._active_macro_path = entry.path
            self._macro_runtime.set_selected_path(entry.path)
        self._macro_panel.set_active_path(self._active_macro_path)
        self._render_trigger_rows()

    def _delete_macro(self, path: Path) -> None:
        """确认后先停止/停用，再请求受控文件服务移入回收站。"""
        if self._hotkey_mgr is not None:
            self._hotkey_mgr.unregister(str(path))
        try:
            self._macro_panel.delete_path_after_stop(path)
        except MacroFileError as exc:
            QMessageBox.warning(self, "删除失败", str(exc))

    @Slot(object, object)
    def _on_active_macro_renamed(self, previous: Path, target: Path) -> None:
        if self._active_macro_path == previous:
            self._active_macro_path = target
            self._macro_runtime.set_selected_path(target)

    def _build_features_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("features_scroll_area")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 14, 18, 18)
        layout.setSpacing(12)

        quick_group = QGroupBox("快捷连点")
        quick_group.setObjectName("quick_click_group")
        quick_row = QHBoxLayout(quick_group)
        quick_row.setContentsMargins(10, 10, 10, 10)
        quick_row.setSpacing(8)
        self._quick_click_enabled = QCheckBox("启用")
        self._quick_click_enabled.setObjectName("quick_click_enabled")
        self._quick_click_enabled.setChecked(self._quick_click_settings.enabled)
        self._quick_click_hotkey = TriggerKeyEdit()
        self._quick_click_hotkey.setObjectName("quick_click_hotkey")
        self._quick_click_hotkey.setFixedWidth(92)
        self._quick_click_hotkey.set_hotkey(self._quick_click_settings.hotkey)
        self._quick_click_mode = QComboBox()
        self._quick_click_mode.setObjectName("quick_click_mode")
        self._quick_click_mode.addItem("按下", "down")
        self._quick_click_mode.addItem("切换", "switch")
        self._quick_click_mode.setCurrentIndex(
            0 if self._quick_click_settings.mode == "down" else 1
        )
        self._quick_click_mode.setFixedWidth(82)
        self._quick_click_interval = RoseSpinBox()
        self._quick_click_interval.setObjectName("quick_click_interval")
        self._quick_click_interval.setRange(1, 10000)
        self._quick_click_interval.setValue(self._quick_click_settings.interval_ms)
        self._quick_click_interval.setSuffix(" ms")
        self._quick_click_interval.setFixedWidth(94)
        quick_row.addWidget(self._quick_click_enabled)
        quick_row.addWidget(QLabel("按键"))
        quick_row.addWidget(self._quick_click_hotkey)
        quick_row.addWidget(QLabel("模式"))
        quick_row.addWidget(self._quick_click_mode)
        quick_row.addWidget(QLabel("间隔"))
        quick_row.addWidget(self._quick_click_interval)
        quick_row.addStretch(1)
        layout.addWidget(quick_group)

        keybind_group = QGroupBox("共享游戏键位")
        keybind_layout = QVBoxLayout(keybind_group)
        keybind_layout.setContentsMargins(8, 8, 8, 8)
        self._game_keybinds_panel = GameKeybindsPanel()
        keybind_layout.addWidget(self._game_keybinds_panel)
        layout.addWidget(keybind_group)
        layout.addStretch(1)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        self._quick_click_enabled.toggled.connect(self._save_quick_click_settings)
        self._quick_click_hotkey.hotkey_selected.connect(self._save_quick_click_settings)
        self._quick_click_mode.currentIndexChanged.connect(self._save_quick_click_settings)
        self._quick_click_interval.valueChanged.connect(self._save_quick_click_settings)
        return page

    @staticmethod
    def _disabled_combo(value: str) -> QComboBox:
        combo = QComboBox()
        combo.addItem(value)
        combo.setEnabled(False)
        return combo

    def _build_settings_page(self) -> QWidget:
        if not hasattr(self, "_sound_effects"):
            # 离屏 UI 测试可直接构建页面；正式入口会在 _setup_ui 前创建它。
            self._sound_effects = SoundEffects()
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("settings_scroll_area")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QFormLayout(content)
        layout.setContentsMargins(40, 28, 90, 28)
        layout.setHorizontalSpacing(28)
        layout.setVerticalSpacing(16)
        self._status_label = QLabel("● 热键已启用")
        self._status_label.setObjectName("global_status_label")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._status_label.setStyleSheet(
            "font-size: 20px; color: #6E4055; font-weight: 600;"
        )
        layout.addRow("当前状态", self._status_label)
        self._global_hotkey_field = TriggerKeyEdit()
        self._global_hotkey_field.setObjectName("global_hotkey_field")
        self._global_hotkey_field.set_hotkey(self._global_hotkey)
        self._global_hotkey_field.hotkey_selected.connect(self._save_global_hotkey)
        layout.addRow("全局开关", self._global_hotkey_field)
        self._osd_enabled_field = QCheckBox("显示 OSD 屏幕提示")
        self._osd_enabled_field.setObjectName("osd_enabled_field")
        self._osd_enabled_field.setChecked(self._osd_popup.popup_enabled)
        self._osd_enabled_field.toggled.connect(self._osd_popup.set_enabled)
        layout.addRow("OSD", self._osd_enabled_field)
        self._sound_enabled_field = QCheckBox("启用提示音（默认开启）")
        self._sound_enabled_field.setChecked(self._sound_effects.enabled)
        self._sound_enabled_field.toggled.connect(self._sound_effects.set_enabled)
        layout.addRow("提示音", self._sound_enabled_field)
        self._theme_selector = QComboBox()
        self._theme_selector.setObjectName("theme_selector")
        for label, value in THEME_OPTIONS:
            self._theme_selector.addItem(label, value)
        self._select_combo_data(self._theme_selector, self._appearance.theme)
        layout.addRow("主题", self._theme_selector)
        self._layout_selector = QComboBox()
        self._layout_selector.setObjectName("layout_selector")
        for label, value in LAYOUT_OPTIONS:
            self._layout_selector.addItem(label, value)
        self._select_combo_data(self._layout_selector, self._appearance.layout)
        layout.addRow("界面布局", self._layout_selector)
        self._appearance_description = QLabel()
        self._appearance_description.setObjectName("appearance_description")
        self._appearance_description.setWordWrap(True)
        layout.addRow("外观说明", self._appearance_description)
        self._restore_appearance_button = QPushButton("恢复经典外观")
        self._restore_appearance_button.setObjectName("restore_classic_appearance")
        self._restore_appearance_button.setToolTip(
            "一次恢复经典粉红主题和经典顶部标签"
        )
        layout.addRow("快速恢复", self._restore_appearance_button)
        info = QLabel(_INSTRUCTION_TEXT)
        info.setWordWrap(True)
        layout.addRow("使用说明", info)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        self._theme_selector.currentIndexChanged.connect(self._on_appearance_changed)
        self._layout_selector.currentIndexChanged.connect(self._on_appearance_changed)
        self._restore_appearance_button.clicked.connect(
            self._restore_classic_appearance
        )
        self._update_appearance_description()
        return page

    def _setup_hotkey(self) -> None:
        self._hotkey_mgr = HotkeyManager(int(self.winId()))
        self._hotkey_mgr.set_global_disable_key(self._global_hotkey)
        self._hotkey_mgr.on_toggle(self._dispatcher.on_toggle_hook)
        self._dispatcher.set_natural_finish_callback(
            lambda hotkey, generation: self._hotkey_mgr.mark_finished(hotkey, generation)
        )
        self._hotkey_mgr.start()
        self._configure_independent_hotkeys()
        self._configure_quick_click_hotkey()
        logger.info(
            "宏触发已就绪：启动默认启用，每个启用宏使用自己的按键，全局键=%s",
            self._global_hotkey,
        )

    def closeEvent(self, event) -> None:
        logger.info("程序退出")
        if self._hotkey_mgr:
            self._hotkey_mgr.stop()
        if getattr(self, "_quick_click_controller", None):
            self._quick_click_controller.shutdown()
        if self._dispatcher:
            self._dispatcher.stop_active_execution()
        keyboard.unhook_all()
        if self._osd_popup:
            self._osd_popup.close()
        QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)

    def eventFilter(self, watched, event) -> bool:
        if (
            not getattr(self, "_focus_sound_played", False)
            and event.type() == QEvent.Type.MouseButtonPress
            and isinstance(watched, QWidget)
            and (watched is self or self.isAncestorOf(watched))
        ):
            self._focus_sound_played = True
            sound_effects = getattr(self, "_sound_effects", None)
            if sound_effects is not None:
                sound_effects.play_selected()
        return super().eventFilter(watched, event)


def _cleanup() -> None:
    try:
        keyboard.unhook_all()
    except Exception:
        pass


atexit.register(_cleanup)


def _is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _set_windows_app_identity() -> None:
    """让 Windows 任务栏不再把本程序归为 python.exe。"""
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_WINDOWS_APP_ID)


def show_startup_window(window: QMainWindow) -> None:
    """启动时把窗口带到前台一次，不改变之后的最小化或隐藏语义。"""
    window.show()
    _activate_startup_window(window)
    QTimer.singleShot(0, lambda: _activate_startup_window(window))


def _activate_startup_window(window: QMainWindow) -> None:
    window.raise_()
    window.activateWindow()
    if sys.platform != "win32" or not hasattr(window, "winId"):
        return
    try:
        hwnd = int(window.winId())
        user32 = ctypes.windll.user32
        flags = 0x0001 | 0x0002 | 0x0040  # NOSIZE | NOMOVE | SHOWWINDOW
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, flags)  # 临时前置
        user32.SetForegroundWindow(hwnd)
        user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, flags)  # 恢复非永久置顶
    except (AttributeError, OSError, TypeError):
        pass


def main() -> int:
    startup_started = _IMPORT_STARTED_AT
    _enable_per_monitor_v2_dpi()
    _set_windows_app_identity()
    instance = SingleInstanceGuard()
    if not instance.acquire():
        show_already_running_message()
        return 0
    try:
        setup_logging()
        logger.info("自动连招启动")
        macro_runtime = PythonMacroRuntime()
        app = QApplication(sys.argv)
        qt_ready = time.perf_counter()
        app.setApplicationName(_APP_TITLE)
        app.setWindowIcon(application_icon())
        if not _is_admin():
            logger.warning("当前未以管理员权限运行，某些游戏可能无法接收模拟输入")
        window = MainWindow(macro_runtime)
        window_ready = time.perf_counter()
        show_startup_window(window)
        logger.info(
            "启动耗时：导入与 Qt %.0fms，窗口与 hook %.0fms，总计 %.0fms",
            (qt_ready - startup_started) * 1000,
            (window_ready - qt_ready) * 1000,
            (time.perf_counter() - startup_started) * 1000,
        )
        return app.exec()
    finally:
        instance.release()


if __name__ == "__main__":
    sys.exit(main())
