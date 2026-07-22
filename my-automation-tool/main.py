"""MyAutoPlayer 程序入口：阶段 3 的单 Python 键盘测试宏。"""
from __future__ import annotations

import atexit
import ctypes
import os
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path

_IMPORT_STARTED_AT = time.perf_counter()

import keyboard
from PySide6.QtCore import (
    QEvent,
    QLibraryInfo,
    QObject,
    Qt,
    QTimer,
    QTranslator,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSlider,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.hotkey_manager import HotkeyManager, TriggerMode
from src.core.audio_devices import list_microphone_devices
from src.core.input_keys import KEYBOARD_KEYS, MOUSE_HOTKEYS, physical_input_name
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
from src.core.replay_settings import (
    REPLAY_DURATIONS,
    REPLAY_ENCODER_MODES,
    REPLAY_FRAME_RATES,
    REPLAY_QUALITIES,
    ReplaySettings,
    ReplaySettingsStore,
)
from src.core.native_replay import (
    NativeAudioPreviewController,
    NativeReplayController,
    normalise_replay_session_name,
)
from src.core.replay_history import ReplayHistoryEntry, ReplayHistoryStore, ReplayHistoryError
from src.ui.macro_library_panel import MacroLibraryPanel
from src.ui.appearance import (
    AppearanceSettings,
    AppearanceSettingsStore,
    stylesheet_for,
)
from src.ui.game_keybinds_panel import GameKeybindsPanel
from src.ui.osd_window import OsdPopup
from src.ui.key_monitor_window import (
    DEFAULT_MONITOR_KEYS,
    DETAIL_BACKGROUND_PRESETS,
    RECENT_COUNTS,
    KeyMonitorWindow,
)
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
from src.utils.app_paths import application_root, log_root, macro_root, resource_root
from src.utils.logger import clear_logs_older_than, get_logger, setup_logging
from src.utils.single_instance import SingleInstanceGuard

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


def macro_run_notification(name: str, count: int) -> str:
    """Describe the planned loop count shown at the macro start edge."""
    loop_text = "+∞" if count == 0 else f"{count} 次"
    return f"{name} 宏运行中 · 循环 {loop_text}"


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
        self._osd_popup.show_notification(
            macro_run_notification(macro.name, macro.count), success=True
        )

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
        self._replay_settings_store = ReplaySettingsStore()
        self._replay_settings = self._replay_settings_store.load()
        self._native_replay_controller = NativeReplayController()
        self._audio_preview_controller = NativeAudioPreviewController()
        self._audio_preview_error: str | None = None
        self._replay_save_task: dict[str, object] | None = None
        self._native_replay_exit_handled = False
        self._recording_flash_on = False
        self._recording_flash_ticks = 0
        self._key_monitor_window: KeyMonitorWindow | None = None
        self._native_replay_timer = QTimer(self)
        self._native_replay_timer.setInterval(100)
        self._native_replay_timer.timeout.connect(self._poll_native_replay)
        self._audio_preview_restart_timer = QTimer(self)
        self._audio_preview_restart_timer.setSingleShot(True)
        self._audio_preview_restart_timer.setInterval(350)
        self._audio_preview_restart_timer.timeout.connect(self._start_audio_preview)
        self._focus_sound_played = False
        self._global_hotkey = self._load_global_hotkey()
        self._setup_ui()
        if os.environ.get("MYAUTOPLAYER_DISABLE_AUDIO") != "1":
            self._start_audio_preview()
            self._native_replay_timer.start()
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
            self._appearance = AppearanceSettings()
        if not hasattr(self, "_replay_settings_store"):
            self._replay_settings_store = ReplaySettingsStore()
        if not hasattr(self, "_replay_settings"):
            self._replay_settings = self._replay_settings_store.load()
        if not hasattr(self, "_native_replay_controller"):
            self._native_replay_controller = NativeReplayController()
        if not hasattr(self, "_audio_preview_controller"):
            self._audio_preview_controller = NativeAudioPreviewController()
        if not hasattr(self, "_audio_preview_error"):
            self._audio_preview_error = None
        if not hasattr(self, "_replay_save_task"):
            self._replay_save_task = None
        if not hasattr(self, "_native_replay_exit_handled"):
            self._native_replay_exit_handled = False
        if not hasattr(self, "_recording_flash_on"):
            self._recording_flash_on = False
        if not hasattr(self, "_recording_flash_ticks"):
            self._recording_flash_ticks = 0
        if not hasattr(self, "_key_monitor_window"):
            self._key_monitor_window = None
        if not hasattr(self, "_native_replay_timer"):
            self._native_replay_timer = QTimer(self)
            self._native_replay_timer.setInterval(100)
            self._native_replay_timer.timeout.connect(self._poll_native_replay)
        if not hasattr(self, "_audio_preview_restart_timer"):
            self._audio_preview_restart_timer = QTimer(self)
            self._audio_preview_restart_timer.setSingleShot(True)
            self._audio_preview_restart_timer.setInterval(350)
            self._audio_preview_restart_timer.timeout.connect(self._start_audio_preview)
        self.setMinimumWidth(760)
        self.setWindowIcon(application_icon())
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setMinimumHeight(510)
        screen = QApplication.primaryScreen()
        if screen is not None:
            self.setMaximumHeight(screen.availableGeometry().height())
            self.setMaximumWidth(screen.availableGeometry().width())
        self.resize(840, 510)

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
        side_navigation.addItems(["宏库", "触发", "功能", "开发连招", "设置"])
        for index in range(side_navigation.count()):
            side_navigation.item(index).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        side_navigation.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side_navigation.setCurrentRow(0)
        side_layout.addWidget(side_navigation, 1)
        content_layout.addWidget(side_panel)

        tabs = QTabWidget()
        tabs.setObjectName("main_tabs")
        tabs.setDocumentMode(True)
        tabs.setUsesScrollButtons(False)
        tabs.addTab(self._build_macro_page(), "宏库")
        tabs.addTab(self._build_trigger_page(), "触发")
        tabs.addTab(self._build_features_page(), "功能")
        tabs.addTab(self._build_combo_development_page(), "开发连招")
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
        """Stage 19 起固定使用樱空花园画册布局。"""
        self.setStyleSheet(stylesheet_for(self._appearance.theme))
        gallery = True
        self._side_panel.setVisible(True)
        self._tabs.tabBar().hide()
        margins = (8, 8, 8, 8)
        self._content_layout.setContentsMargins(*margins)
        self._content_layout.setSpacing(8 if gallery else 0)
        self.setMinimumWidth(760)
        if fit_layout:
            self.resize(840, self.height())
        if hasattr(self, "_trigger_detail"):
            self._trigger_detail.setFixedWidth(140 if gallery else 134)
        if hasattr(self, "_trigger_table"):
            widths = (40, 76, 68, 54) if gallery else (38, 70, 62, 44)
            for column, width in zip((0, 2, 3, 4), widths):
                self._trigger_table.setColumnWidth(column, width)
        if persist:
            try:
                self._appearance_store.save(self._appearance)
            except OSError as exc:
                logger.warning("外观设置保存失败：%s", exc)
            self._center_on_screen()

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
        enabled = not entry.macro.enabled
        try:
            # 不依赖当前选中行：源码同样允许直接点击任意行的状态开关。
            self._macro_panel.update_trigger_settings(
                entry.path,
                hotkey=entry.macro.hotkey,
                mode=entry.macro.mode,
                count=entry.macro.count,
                speed=entry.macro.speed,
                enabled=enabled,
            )
        except MacroFileError as exc:
            QMessageBox.warning(self, "保存触发设置失败", str(exc))
            return
        self._osd_popup.show_notification(
            f"{entry.macro.name} 已{'启用' if enabled else '禁用'}",
            success=enabled,
        )

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
        enabled = bool(self._trigger_status_field.currentData())
        status_changed = enabled != entry.macro.enabled
        try:
            self._macro_panel.update_trigger_settings(
                entry.path,
                hotkey=hotkey,
                mode=self._trigger_mode_field.currentData(),
                count=self._trigger_count_field.value(),
                speed=self._trigger_speed_field.value(),
                enabled=enabled,
            )
        except MacroFileError as exc:
            QMessageBox.warning(self, "保存触发设置失败", str(exc))
            return
        if status_changed:
            self._osd_popup.show_notification(
                f"{entry.macro.name} 已{'启用' if enabled else '禁用'}",
                success=enabled,
            )

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

    def _build_combo_development_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("combo_development_scroll_area")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        heading = QLabel("开发连招 · 原生回放工作台")
        heading.setObjectName("combo_development_heading")
        heading.setStyleSheet("font-size: 20px; font-weight: 700; color: #A84F6D;")
        layout.addWidget(heading)
        summary = QLabel(
            "未来将由 MyAutoPlayer 自己完成游戏画面、声音和物理按键时间线记录，"
            "不会调用 OBS。战斗时只运行一份编码，保存后生成独立外挂字幕。"
        )
        summary.setWordWrap(True)
        summary.setObjectName("combo_development_summary")
        layout.addWidget(summary)

        settings_group = QGroupBox("回放设置")
        settings_form = QFormLayout(settings_group)
        settings_form.setHorizontalSpacing(18)
        settings_form.setVerticalSpacing(12)

        detected_core = self._native_replay_controller.executable_for(
            self._replay_settings
        )
        self._replay_core_path = QLineEdit(
            str(detected_core) if detected_core is not None else "未找到录像核心"
        )
        self._replay_core_path.setObjectName("replay_core_path")
        self._replay_core_path.setReadOnly(True)
        self._choose_replay_core_button = QPushButton("选择录像核心")
        self._choose_replay_core_button.setObjectName("choose_replay_core_button")
        self._auto_replay_core_button = QPushButton("自动检测")
        self._auto_replay_core_button.setObjectName("auto_replay_core_button")
        core_row = QWidget()
        core_layout = QHBoxLayout(core_row)
        core_layout.setContentsMargins(0, 0, 0, 0)
        core_layout.addWidget(self._replay_core_path, 1)
        core_layout.addWidget(self._choose_replay_core_button)
        core_layout.addWidget(self._auto_replay_core_button)
        settings_form.addRow("录像核心", core_row)

        self._replay_save_directory = QLineEdit(str(self._replay_settings.save_directory))
        self._replay_save_directory.setObjectName("replay_save_directory")
        self._replay_save_directory.setReadOnly(True)
        self._replay_save_directory.setToolTip(str(self._replay_settings.save_directory))
        self._choose_replay_directory_button = QPushButton("选择保存目录")
        self._choose_replay_directory_button.setObjectName("choose_replay_directory_button")
        self._open_replay_directory_button = QPushButton("打开视频保存目录")
        self._open_replay_directory_button.setObjectName("open_replay_directory_button")
        directory_row = QWidget()
        directory_layout = QHBoxLayout(directory_row)
        directory_layout.setContentsMargins(0, 0, 0, 0)
        directory_layout.addWidget(self._replay_save_directory, 1)
        directory_layout.addWidget(self._choose_replay_directory_button)
        directory_layout.addWidget(self._open_replay_directory_button)
        settings_form.addRow("视频保存地址", directory_row)

        self._replay_duration = QComboBox()
        self._replay_duration.setObjectName("replay_duration_selector")
        for minutes in REPLAY_DURATIONS:
            self._replay_duration.addItem(f"保留过去 {minutes} 分钟", minutes)
        self._select_combo_data(self._replay_duration, self._replay_settings.duration_minutes)
        settings_form.addRow("回放时长", self._replay_duration)

        self._replay_monitor = QComboBox()
        self._replay_monitor.setObjectName("replay_monitor_selector")
        screens = QApplication.screens()
        for index, screen in enumerate(screens, start=1):
            size = screen.geometry().size()
            self._replay_monitor.addItem(
                f"显示器 {index}：{screen.name()}（{size.width()}×{size.height()}）",
                index,
            )
        if self._replay_monitor.count() == 0:
            self._replay_monitor.addItem("显示器 1（全局桌面）", 1)
        self._select_combo_data(
            self._replay_monitor, self._replay_settings.monitor_index
        )
        settings_form.addRow("录制画面", self._replay_monitor)

        self._replay_quality = QComboBox()
        self._replay_quality.setObjectName("replay_quality_selector")
        for quality in REPLAY_QUALITIES:
            suffix = "（性能优先默认）" if quality == "1080p" else ""
            self._replay_quality.addItem(f"{quality}{suffix}", quality)
        self._select_combo_data(self._replay_quality, self._replay_settings.quality)
        settings_form.addRow("录制清晰度", self._replay_quality)

        self._replay_fps = QComboBox()
        self._replay_fps.setObjectName("replay_fps_selector")
        for fps in REPLAY_FRAME_RATES:
            suffix = "（性能测试推荐）" if fps == 15 else ""
            self._replay_fps.addItem(f"{fps} 帧/秒{suffix}", fps)
        self._select_combo_data(self._replay_fps, self._replay_settings.fps)
        settings_form.addRow("录制帧率", self._replay_fps)

        self._replay_encoder_mode = QComboBox()
        self._replay_encoder_mode.setObjectName("replay_encoder_mode_selector")
        encoder_labels = {
            "gpu": "GPU 硬件编码（推荐，性能优先）",
            "cpu": "CPU 软件编码（兼容模式，占用较高）",
        }
        for encoder_mode in REPLAY_ENCODER_MODES:
            self._replay_encoder_mode.addItem(encoder_labels[encoder_mode], encoder_mode)
        self._select_combo_data(self._replay_encoder_mode, self._replay_settings.encoder_mode)
        self._replay_encoder_mode.setToolTip(
            "GPU 不可用时程序会明确报错，不会偷偷切换到 CPU；需要 CPU 时请手动选择。"
        )
        settings_form.addRow("编码模式", self._replay_encoder_mode)

        self._record_microphone = QCheckBox("录制麦克风声音（可选，默认关闭）")
        self._record_microphone.setObjectName("record_microphone_checkbox")
        self._record_microphone.setChecked(self._replay_settings.record_microphone)
        self._record_microphone.setToolTip(
            "开启后使用你选择的麦克风，并作为独立音轨保存；关闭时只录桌面声音。"
        )
        microphone_row = QWidget()
        microphone_layout = QVBoxLayout(microphone_row)
        microphone_layout.setContentsMargins(0, 0, 0, 0)
        microphone_layout.setSpacing(3)
        microphone_layout.addWidget(self._record_microphone)
        microphone_device_row = QWidget()
        microphone_device_layout = QHBoxLayout(microphone_device_row)
        microphone_device_layout.setContentsMargins(0, 0, 0, 0)
        self._microphone_device_name = QLineEdit(
            self._replay_settings.microphone_device_name or "系统默认麦克风"
        )
        self._microphone_device_name.setObjectName("microphone_device_name")
        self._microphone_device_name.setReadOnly(True)
        self._choose_microphone_device_button = QPushButton("选择麦克风设备")
        self._choose_microphone_device_button.setObjectName(
            "choose_microphone_device_button"
        )
        microphone_device_layout.addWidget(self._microphone_device_name, 1)
        microphone_device_layout.addWidget(self._choose_microphone_device_button)
        microphone_layout.addWidget(microphone_device_row)
        microphone_gain_row = QWidget()
        microphone_gain_layout = QHBoxLayout(microphone_gain_row)
        microphone_gain_layout.setContentsMargins(0, 0, 0, 0)
        self._microphone_gain = QSlider(Qt.Orientation.Horizontal)
        self._microphone_gain.setObjectName("microphone_gain_slider")
        self._microphone_gain.setRange(0, 200)
        self._microphone_gain.setValue(self._replay_settings.microphone_gain_percent)
        self._microphone_gain_value = QLabel(
            f"{self._replay_settings.microphone_gain_percent}%"
        )
        self._microphone_gain_value.setObjectName("microphone_gain_value")
        microphone_gain_layout.addWidget(QLabel("麦克风音量"))
        microphone_gain_layout.addWidget(self._microphone_gain, 1)
        microphone_gain_layout.addWidget(self._microphone_gain_value)
        microphone_layout.addWidget(microphone_gain_row)
        microphone_note = QLabel(
            "麦克风开启时将作为独立音轨 2 保存；桌面/游戏声音固定为独立音轨 1。"
        )
        microphone_note.setObjectName("record_microphone_status")
        microphone_note.setWordWrap(True)
        microphone_layout.addWidget(microphone_note)
        settings_form.addRow("麦克风", microphone_row)
        layout.addWidget(settings_group)

        audio_status_group = QGroupBox("实时声音状态")
        audio_status_layout = QFormLayout(audio_status_group)
        self._desktop_audio_meter = QProgressBar()
        self._desktop_audio_meter.setObjectName("desktop_audio_meter")
        self._desktop_audio_meter.setRange(0, 100)
        self._desktop_audio_meter.setValue(0)
        self._desktop_audio_meter.setFormat("正在启动设备预检")
        self._microphone_audio_meter = QProgressBar()
        self._microphone_audio_meter.setObjectName("microphone_audio_meter")
        self._microphone_audio_meter.setRange(0, 100)
        self._microphone_audio_meter.setValue(0)
        self._microphone_audio_meter.setFormat("正在启动设备预检")
        audio_status_layout.addRow("桌面声音（音轨 1）", self._desktop_audio_meter)
        audio_status_layout.addRow("麦克风（音轨 2）", self._microphone_audio_meter)
        audio_preview_note = QLabel(
            "未录制时只检测桌面声和所选麦克风的真实音量，不保存声音；开始录像后才按上方设置写入音轨。"
        )
        audio_preview_note.setObjectName("audio_preview_note")
        audio_preview_note.setWordWrap(True)
        audio_status_layout.addRow("设备预检", audio_preview_note)
        layout.addWidget(audio_status_group)

        key_window_group = QGroupBox("实时按键窗口")
        key_window_layout = QVBoxLayout(key_window_group)
        key_window_help = QLabel(
            "在桌面右上角显示常用物理按键；按下会高亮，并显示按住和松开毫秒。"
        )
        key_window_help.setWordWrap(True)
        key_window_layout.addWidget(key_window_help)
        key_window_actions = QHBoxLayout()
        self._open_key_monitor_button = QPushButton("打开按键记录窗口")
        self._open_key_monitor_button.setObjectName("open_key_monitor_button")
        self._configure_key_monitor_button = QPushButton("设置显示按键")
        self._configure_key_monitor_button.setObjectName("configure_key_monitor_button")
        key_window_actions.addWidget(self._open_key_monitor_button)
        key_window_actions.addWidget(self._configure_key_monitor_button)
        key_window_actions.addStretch(1)
        key_window_layout.addLayout(key_window_actions)
        layout.addWidget(key_window_group)

        controls_group = QGroupBox("原生录像核心")
        controls_layout = QVBoxLayout(controls_group)
        native_available = detected_core is not None
        self._native_replay_status = QLabel(
            f"原生录像核心已就绪：{detected_core}。将录制所选显示器的全局画面和全局物理按键。"
            if native_available
            else "尚未找到录像核心。请点击“选择录像核心”，选择 myautoplayer-native-replay.exe。"
        )
        self._native_replay_status.setObjectName("native_replay_status")
        self._native_replay_status.setWordWrap(True)
        controls_layout.addWidget(self._native_replay_status)
        control_row = QHBoxLayout()
        self._start_native_replay_button = QPushButton("开始")
        self._start_native_replay_button.setObjectName("start_native_replay_button")
        self._start_native_replay_button.setEnabled(native_available)
        self._save_native_replay_button = QPushButton("保留过往")
        self._save_native_replay_button.setObjectName("save_native_replay_button")
        self._save_native_replay_button.setEnabled(False)
        control_row.addWidget(self._start_native_replay_button)
        control_row.addWidget(self._save_native_replay_button)
        self._recording_indicator = QPushButton("● 未录制")
        self._recording_indicator.setObjectName("recording_indicator")
        self._recording_indicator.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._recording_indicator.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self._recording_indicator.setToolTip("开始录制后会持续闪烁，仅用于提示状态")
        control_row.addWidget(self._recording_indicator)
        control_row.addStretch(1)
        controls_layout.addLayout(control_row)
        layout.addWidget(controls_group)

        history_group = QGroupBox("历史录像")
        history_layout = QVBoxLayout(history_group)
        self._replay_history_summary = QLabel(
            "按日期读取当前视频保存地址；播放原始视频时，同名 raw.ass 可由支持的播放器自动载入。"
        )
        self._replay_history_summary.setObjectName("replay_history_summary")
        self._replay_history_summary.setWordWrap(True)
        history_layout.addWidget(self._replay_history_summary)
        self._replay_history_table = QTableWidget(0, 7)
        self._replay_history_table.setObjectName("replay_history_table")
        self._replay_history_table.setHorizontalHeaderLabels(
            ["保存时间", "会话名称", "实际时长", "画面", "编码器", "音轨", "状态"]
        )
        self._replay_history_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._replay_history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._replay_history_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._replay_history_table.setAlternatingRowColors(True)
        self._replay_history_table.verticalHeader().setVisible(False)
        self._replay_history_table.setMinimumHeight(220)
        history_header = self._replay_history_table.horizontalHeader()
        history_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        history_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in range(2, 7):
            history_header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        history_layout.addWidget(self._replay_history_table)
        history_actions = QHBoxLayout()
        self._refresh_replay_history_button = QPushButton("刷新历史")
        self._refresh_replay_history_button.setObjectName(
            "refresh_replay_history_button"
        )
        self._play_replay_history_button = QPushButton("播放原始视频")
        self._play_replay_history_button.setObjectName("play_replay_history_button")
        self._open_replay_subtitle_button = QPushButton("打开外挂字幕")
        self._open_replay_subtitle_button.setObjectName("open_replay_subtitle_button")
        self._open_replay_session_button = QPushButton("打开会话目录")
        self._open_replay_session_button.setObjectName("open_replay_session_button")
        self._delete_replay_history_button = QPushButton("删除所选会话")
        self._delete_replay_history_button.setObjectName(
            "delete_replay_history_button"
        )
        history_actions.addWidget(self._refresh_replay_history_button)
        history_actions.addWidget(self._play_replay_history_button)
        history_actions.addWidget(self._open_replay_subtitle_button)
        history_actions.addWidget(self._open_replay_session_button)
        history_actions.addWidget(self._delete_replay_history_button)
        history_actions.addStretch(1)
        history_layout.addLayout(history_actions)
        layout.addWidget(history_group)
        layout.addStretch(1)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        self._choose_replay_directory_button.clicked.connect(self._choose_replay_directory)
        self._open_replay_directory_button.clicked.connect(self._open_replay_directory)
        self._choose_replay_core_button.clicked.connect(self._choose_replay_core)
        self._auto_replay_core_button.clicked.connect(self._auto_detect_replay_core)
        self._replay_duration.currentIndexChanged.connect(self._save_replay_settings)
        self._replay_monitor.currentIndexChanged.connect(self._save_replay_settings)
        self._replay_quality.currentIndexChanged.connect(self._save_replay_settings)
        self._replay_fps.currentIndexChanged.connect(self._save_replay_settings)
        self._replay_encoder_mode.currentIndexChanged.connect(self._save_replay_settings)
        self._record_microphone.toggled.connect(self._save_replay_settings)
        self._microphone_gain.valueChanged.connect(self._on_microphone_gain_changed)
        self._choose_microphone_device_button.clicked.connect(
            self._choose_microphone_device
        )
        self._start_native_replay_button.clicked.connect(self._toggle_native_replay)
        self._save_native_replay_button.clicked.connect(self._save_native_replay)
        self._refresh_replay_history_button.clicked.connect(
            self._refresh_replay_history
        )
        self._play_replay_history_button.clicked.connect(
            self._play_selected_replay_history
        )
        self._open_replay_subtitle_button.clicked.connect(
            self._open_selected_replay_subtitle
        )
        self._open_replay_session_button.clicked.connect(
            self._open_selected_replay_directory
        )
        self._delete_replay_history_button.clicked.connect(
            self._delete_selected_replay_history
        )
        self._replay_history_table.itemSelectionChanged.connect(
            self._update_replay_history_actions
        )
        self._open_key_monitor_button.clicked.connect(self._open_key_monitor)
        self._configure_key_monitor_button.clicked.connect(
            self._configure_key_monitor
        )
        self._refresh_replay_history()
        return page

    def _ensure_key_monitor(self) -> KeyMonitorWindow:
        if self._key_monitor_window is None:
            self._key_monitor_window = KeyMonitorWindow()
            self._key_monitor_window.closed.connect(self._on_key_monitor_closed)
        return self._key_monitor_window

    def _open_key_monitor(self) -> None:
        monitor = self._ensure_key_monitor()
        hotkey_manager = getattr(self, "_hotkey_mgr", None)
        if hotkey_manager is not None:
            hotkey_manager.add_physical_observer(monitor.observe_input)
        monitor.show()
        monitor.raise_()

    def _on_key_monitor_closed(self) -> None:
        monitor = self._key_monitor_window
        hotkey_manager = getattr(self, "_hotkey_mgr", None)
        if monitor is not None and hotkey_manager is not None:
            hotkey_manager.remove_physical_observer(monitor.observe_input)
        self._key_monitor_window = None

    def _configure_key_monitor(self) -> None:
        self._open_key_monitor()
        monitor = self._ensure_key_monitor()
        dialog = QDialog(self)
        dialog.setWindowTitle("设置按键记录窗口")
        dialog.resize(460, 640)
        layout = QVBoxLayout(dialog)
        note = QLabel(
            "常用键首次默认勾选，也可以按你的习惯取消。"
            "再次打开时，所有勾选状态都会保留；额外键排列在鼠标右侧。"
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        recent_row = QHBoxLayout()
        recent_row.addWidget(QLabel("最近事件显示："))
        recent_count = QComboBox()
        recent_count.setObjectName("key_monitor_recent_count")
        for count in RECENT_COUNTS:
            recent_count.addItem(f"{count} 个", count)
        recent_count.setCurrentIndex(recent_count.findData(monitor.recent_count))
        recent_row.addWidget(recent_count)
        recent_row.addStretch(1)
        layout.addLayout(recent_row)

        appearance_form = QFormLayout()
        detail_background = QComboBox()
        detail_background.setObjectName("key_monitor_detail_background")
        for preset, (label, _rgb) in DETAIL_BACKGROUND_PRESETS.items():
            detail_background.addItem(label, preset)
        detail_background.setCurrentIndex(
            detail_background.findData(monitor.detail_background)
        )
        appearance_form.addRow("详情板块背景：", detail_background)

        detail_opacity = QSlider(Qt.Orientation.Horizontal)
        detail_opacity.setObjectName("key_monitor_detail_opacity")
        detail_opacity.setRange(0, 100)
        detail_opacity.setValue(monitor.detail_opacity)
        detail_opacity_value = QLabel(f"{monitor.detail_opacity}%")
        detail_opacity.valueChanged.connect(
            lambda value: detail_opacity_value.setText(f"{value}%")
        )
        detail_opacity_row = QHBoxLayout()
        detail_opacity_row.addWidget(detail_opacity, 1)
        detail_opacity_row.addWidget(detail_opacity_value)
        appearance_form.addRow("板块深浅：", detail_opacity_row)

        window_opacity = QSlider(Qt.Orientation.Horizontal)
        window_opacity.setObjectName("key_monitor_window_opacity")
        window_opacity.setRange(0, 100)
        window_opacity.setValue(monitor.window_opacity)
        window_opacity_value = QLabel(f"{monitor.window_opacity}%")
        window_opacity.valueChanged.connect(
            lambda value: window_opacity_value.setText(f"{value}%")
        )
        window_opacity_row = QHBoxLayout()
        window_opacity_row.addWidget(window_opacity, 1)
        window_opacity_row.addWidget(window_opacity_value)
        appearance_form.addRow("整体窗口透明度：", window_opacity_row)
        layout.addLayout(appearance_form)

        layout.addWidget(QLabel("显示按键（最多32个）："))
        key_list = QListWidget()
        key_list.setObjectName("key_monitor_selected_keys")
        key_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        current = set(monitor.keys)
        available = list(
            dict.fromkeys(
                (*DEFAULT_MONITOR_KEYS, *monitor.keys, *sorted(KEYBOARD_KEYS), *sorted(MOUSE_HOTKEYS))
            )
        )
        for key in available:
            item = QListWidgetItem(physical_input_name(key))
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(
                Qt.CheckState.Checked if key in current else Qt.CheckState.Unchecked
            )
            key_list.addItem(item)
        layout.addWidget(key_list)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        apply_button = buttons.button(QDialogButtonBox.StandardButton.Apply)
        ok_button.setText("确定")
        cancel_button.setText("取消")
        apply_button.setText("应用")
        apply_button.setObjectName("key_monitor_apply_button")
        apply_button.setEnabled(False)
        layout.addWidget(buttons)

        def control_state() -> tuple[tuple[str, ...], int, str, int, int]:
            selected = tuple(
                key_list.item(index).data(Qt.ItemDataRole.UserRole)
                for index in range(key_list.count())
                if key_list.item(index).checkState() == Qt.CheckState.Checked
            )
            return (
                selected,
                int(recent_count.currentData()),
                str(detail_background.currentData()),
                int(detail_opacity.value()),
                int(window_opacity.value()),
            )

        committed_state = [
            (
                monitor.keys,
                monitor.recent_count,
                monitor.detail_background,
                monitor.detail_opacity,
                monitor.window_opacity,
            )
        ]

        def preview(signal_value=None) -> None:
            state = (
                signal_value
                if isinstance(signal_value, tuple) and len(signal_value) == 5
                else control_state()
            )
            keys, count, background, detail_alpha, window_alpha = state
            monitor.set_keys(keys, persist=False)
            monitor.set_recent_count(count, persist=False)
            monitor.set_appearance(
                background,
                detail_alpha,
                window_alpha,
                persist=False,
            )
            apply_button.setEnabled(control_state() != committed_state[0])

        def apply_changes() -> None:
            preview()
            monitor.save_settings()
            committed_state[0] = control_state()
            apply_button.setEnabled(False)

        def accept_changes() -> None:
            apply_changes()
            dialog.accept()

        def reject_changes() -> None:
            preview(committed_state[0])
            apply_button.setEnabled(False)
            dialog.reject()

        recent_count.currentIndexChanged.connect(preview)
        detail_background.currentIndexChanged.connect(preview)
        detail_opacity.valueChanged.connect(preview)
        window_opacity.valueChanged.connect(preview)
        key_list.itemChanged.connect(preview)
        apply_button.clicked.connect(apply_changes)
        buttons.accepted.connect(accept_changes)
        buttons.rejected.connect(reject_changes)

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            apply_changes()
        else:
            preview(committed_state[0])

    def _toggle_native_replay(self) -> None:
        if self._replay_save_task is not None:
            return
        if self._native_replay_controller.running:
            self._native_replay_controller.request_stop()
            self._native_replay_status.setText(
                "正在停止录像并清空临时回放缓冲……\n"
                "不会弹出命名窗口，也不会生成正式录像。"
            )
            self._start_native_replay_button.setEnabled(False)
            self._save_native_replay_button.setEnabled(False)
            return
        self._audio_preview_restart_timer.stop()
        self._audio_preview_controller.stop()
        try:
            session = self._native_replay_controller.start(
                self._replay_settings
            )
        except (OSError, RuntimeError, ValueError) as exc:
            QMessageBox.warning(self, "无法开始原生录像", str(exc))
            self._schedule_audio_preview_restart()
            return
        self._native_replay_exit_handled = False
        hotkey_manager = getattr(self, "_hotkey_mgr", None)
        if hotkey_manager is not None:
            hotkey_manager.add_physical_observer(
                self._native_replay_controller.observe_input
            )
        self._native_replay_status.setText(
            f"回放缓冲正在运行：{session.directory}\n"
            f"点击“保留过往”会保存最近 {self._replay_settings.duration_minutes} 分钟，保存时不会停止录像。"
        )
        self._set_replay_controls_enabled(False)
        self._start_native_replay_button.setText("停止并清空")
        self._save_native_replay_button.setEnabled(True)
        self._native_replay_timer.start()

    def _save_native_replay(self) -> None:
        if not self._native_replay_controller.running or self._replay_save_task is not None:
            return
        session_name = self._ask_replay_session_name()
        if session_name is None:
            return
        self._start_replay_export(session_name)

    def _start_replay_export(self, session_name: str) -> None:
        result: dict[str, object] = {"session": None, "error": None}

        def export() -> None:
            try:
                result["session"] = self._native_replay_controller.save_recent(
                    self._replay_settings,
                    session_name,
                    duration_minutes=self._replay_settings.duration_minutes,
                )
            except Exception as exc:  # surfaced in the Qt thread below
                result["error"] = exc

        thread = threading.Thread(target=export, daemon=True, name="replay-save-recent")
        self._replay_save_task = {
            "thread": thread,
            "result": result,
        }
        self._start_native_replay_button.setEnabled(False)
        self._save_native_replay_button.setEnabled(False)
        self._native_replay_status.setText(
            f"正在后台生成“{session_name}”的最近 {self._replay_settings.duration_minutes} 分钟回放……\n"
            "录像缓冲仍在继续，不会漏掉后续操作。"
        )
        thread.start()
        self._native_replay_timer.start()

    def _poll_replay_export(self) -> bool:
        task = self._replay_save_task
        if task is None:
            return False
        thread = task["thread"]
        if isinstance(thread, threading.Thread) and thread.is_alive():
            return True
        result = task["result"]
        self._replay_save_task = None
        error = result.get("error") if isinstance(result, dict) else None
        session = result.get("session") if isinstance(result, dict) else None
        if error is not None:
            QMessageBox.warning(self, "保留过往失败", str(error))
            self._native_replay_status.setText(f"保留过往失败：{error}")
        elif session is not None:
            self._native_replay_status.setText(
                f"原始视频：{session.raw_video}\n"
                f"自动样式字幕：{session.input_subtitles}\n"
                f"兼容字幕：{session.preview_subtitles}\n"
                "最终交付为一份原始视频和外挂字幕，不再生成 perfect.mp4。"
            )
            self._refresh_replay_history()
        running = self._native_replay_controller.running
        self._start_native_replay_button.setEnabled(running)
        self._save_native_replay_button.setEnabled(running)
        return False

    def _poll_native_replay(self) -> None:
        self._poll_replay_export()
        self._update_replay_live_status()
        if self._native_replay_controller.running:
            return
        if self._native_replay_exit_handled:
            return
        return_code = self._native_replay_controller.poll()
        if return_code is None:
            return
        self._native_replay_exit_handled = True
        hotkey_manager = getattr(self, "_hotkey_mgr", None)
        if hotkey_manager is not None:
            hotkey_manager.remove_physical_observer(
                self._native_replay_controller.observe_input
            )
        if return_code == 0:
            self._native_replay_controller.cleanup_buffer()
            self._native_replay_status.setText(
                "录像已停止，临时回放缓冲已清空。\n"
                "只有点击“保留过往”才会命名并生成正式录像。"
            )
            self._start_native_replay_button.setText("再次录制")
            self._set_replay_controls_enabled(True)
            self._start_native_replay_button.setEnabled(True)
            self._save_native_replay_button.setEnabled(False)
            self._native_replay_timer.stop()
        else:
            buffer = self._native_replay_controller.buffer
            log_path = buffer.native_log if buffer is not None else "未知"
            detail = ""
            if buffer is not None and buffer.native_log.is_file():
                try:
                    lines = buffer.native_log.read_text(
                        encoding="utf-8", errors="replace"
                    ).splitlines()
                    if lines:
                        detail = f"\n原因：{lines[-1]}"
                except OSError:
                    pass
            self._native_replay_status.setText(
                f"原生录像失败（退出码 {return_code}）。{detail}\n日志：{log_path}"
            )
            self._start_native_replay_button.setText("再次录制")
            self._set_replay_controls_enabled(True)
            self._start_native_replay_button.setEnabled(True)
            self._save_native_replay_button.setEnabled(False)
            self._native_replay_timer.stop()
        self._schedule_audio_preview_restart()

    def _ask_replay_session_name(self) -> str | None:
        value, accepted = QInputDialog.getText(
            self,
            "给本次录像文件夹命名",
            "请输入容易识别的名称。\n例如输入“秧秧完美连招”，将保存为：\n"
            "秧秧完美连招-20260721-013628-recording",
            QLineEdit.EchoMode.Normal,
            "精彩连招",
        )
        if not accepted:
            return None
        try:
            return normalise_replay_session_name(value)
        except ValueError as exc:
            QMessageBox.warning(self, "录像文件夹名称无效", str(exc))
            return None

    def _set_replay_controls_enabled(self, enabled: bool) -> None:
        """Keep one rolling buffer internally compatible from start to stop."""
        for control in (
            self._replay_duration,
            self._replay_monitor,
            self._replay_quality,
            self._replay_fps,
            self._replay_encoder_mode,
            self._record_microphone,
            self._choose_microphone_device_button,
            self._microphone_gain,
            self._choose_replay_directory_button,
            self._choose_replay_core_button,
            self._auto_replay_core_button,
        ):
            control.setEnabled(enabled)

    def _save_replay_settings(self, *_unused) -> None:
        previous_save_directory = self._replay_settings.save_directory
        try:
            saved = self._replay_settings_store.save(
                ReplaySettings(
                    Path(self._replay_save_directory.text()),
                    int(self._replay_duration.currentData()),
                    str(self._replay_quality.currentData()),
                    str(self._replay_encoder_mode.currentData()),
                    int(self._replay_fps.currentData()),
                    int(self._replay_monitor.currentData()),
                    self._replay_settings.core_path,
                    self._record_microphone.isChecked(),
                    self._replay_settings.microphone_device_id,
                    self._replay_settings.microphone_device_name,
                    int(self._microphone_gain.value()),
                )
            )
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.warning(self, "回放设置未保存", str(exc))
            return
        self._replay_settings = saved
        self._replay_save_directory.setText(str(saved.save_directory))
        self._replay_save_directory.setToolTip(str(saved.save_directory))
        if (
            saved.save_directory != previous_save_directory
            and hasattr(self, "_replay_history_table")
        ):
            self._refresh_replay_history()
        self._schedule_audio_preview_restart()

    def _on_microphone_gain_changed(self, value: int) -> None:
        self._microphone_gain_value.setText(f"{value}%")
        self._save_replay_settings()

    def _schedule_audio_preview_restart(self) -> None:
        if os.environ.get("MYAUTOPLAYER_DISABLE_AUDIO") == "1":
            return
        if self._native_replay_controller.running:
            return
        self._audio_preview_restart_timer.start()

    def _start_audio_preview(self) -> None:
        if os.environ.get("MYAUTOPLAYER_DISABLE_AUDIO") == "1":
            return
        if self._native_replay_controller.running:
            return
        try:
            self._audio_preview_controller.start(self._replay_settings)
        except (OSError, RuntimeError, ValueError) as exc:
            self._audio_preview_error = str(exc)
        else:
            self._audio_preview_error = None
        self._native_replay_timer.start()

    def _update_replay_live_status(self) -> None:
        running = self._native_replay_controller.running
        if running:
            self._recording_flash_ticks = (self._recording_flash_ticks + 1) % 5
            if self._recording_flash_ticks == 0:
                self._recording_flash_on = not self._recording_flash_on
            if self._recording_flash_on:
                self._recording_indicator.setText("● 正在录制")
                self._recording_indicator.setStyleSheet(
                    "QPushButton { color: white; background: #D85C82; border: 1px solid #F5B6CA; font-weight: 700; }"
                )
            else:
                self._recording_indicator.setText("◉ 正在录制")
                self._recording_indicator.setStyleSheet(
                    "QPushButton { color: #7D314C; background: #FBE3EC; border: 1px solid #DDA0B5; font-weight: 700; }"
                )
            desktop_level, microphone_level = self._native_replay_controller.audio_levels()
            self._desktop_audio_meter.setValue(desktop_level)
            self._desktop_audio_meter.setFormat(
                f"桌面有声音 · {desktop_level}%" if desktop_level else "桌面静音 · 0%"
            )
            self._microphone_audio_meter.setValue(microphone_level)
            if self._replay_settings.record_microphone:
                self._microphone_audio_meter.setFormat(
                    f"麦克风有声音 · {microphone_level}%" if microphone_level else "麦克风静音 · 0%"
                )
            else:
                self._microphone_audio_meter.setFormat("未录制")
        else:
            self._recording_flash_on = False
            self._recording_flash_ticks = 0
            self._recording_indicator.setText("● 未录制")
            self._recording_indicator.setStyleSheet("")
            preview_return_code = self._audio_preview_controller.poll()
            if preview_return_code not in (None, 0):
                self._audio_preview_error = self._audio_preview_controller.last_error
            if self._audio_preview_controller.running:
                desktop_level, microphone_level = self._audio_preview_controller.audio_levels()
                self._desktop_audio_meter.setValue(desktop_level)
                self._desktop_audio_meter.setFormat(
                    f"设备预检 · {desktop_level}% · 不保存"
                )
                self._microphone_audio_meter.setValue(microphone_level)
                microphone_action = "录像时保存" if self._replay_settings.record_microphone else "当前不保存"
                self._microphone_audio_meter.setFormat(
                    f"设备预检 · {microphone_level}% · {microphone_action}"
                )
            else:
                self._desktop_audio_meter.setValue(0)
                self._microphone_audio_meter.setValue(0)
                status = self._audio_preview_error or "正在启动设备预检"
                self._desktop_audio_meter.setFormat(status)
                self._microphone_audio_meter.setFormat(status)

    def _choose_microphone_device(self) -> None:
        try:
            devices = list_microphone_devices()
        except Exception as exc:
            QMessageBox.warning(self, "无法读取麦克风设备", str(exc))
            return
        if not devices:
            QMessageBox.warning(
                self,
                "没有可用麦克风",
                "Windows 当前没有返回可用的麦克风输入设备，请检查连接和麦克风权限。",
            )
            return
        labels: list[str] = []
        occurrences: dict[str, int] = {}
        for device in devices:
            base = f"{device.name}（系统默认）" if device.is_default else device.name
            occurrences[base] = occurrences.get(base, 0) + 1
            suffix = f"（{occurrences[base]}）" if occurrences[base] > 1 else ""
            labels.append(base + suffix)
        current_index = next(
            (
                index
                for index, device in enumerate(devices)
                if device.identifier == self._replay_settings.microphone_device_id
            ),
            0,
        )
        selected, accepted = QInputDialog.getItem(
            self,
            "选择麦克风设备",
            "请选择录制语音时使用的麦克风：",
            labels,
            current_index,
            False,
        )
        if not accepted:
            return
        device = devices[labels.index(selected)]
        self._replay_settings = self._replay_settings_store.save(
            ReplaySettings(
                self._replay_settings.save_directory,
                self._replay_settings.duration_minutes,
                self._replay_settings.quality,
                self._replay_settings.encoder_mode,
                self._replay_settings.fps,
                self._replay_settings.monitor_index,
                self._replay_settings.core_path,
                self._replay_settings.record_microphone,
                device.identifier,
                device.name,
                self._replay_settings.microphone_gain_percent,
            )
        )
        self._microphone_device_name.setText(device.name)
        self._microphone_device_name.setToolTip(device.name)
        self._schedule_audio_preview_restart()

    def _choose_replay_core(self) -> None:
        selected, _filter = QFileDialog.getOpenFileName(
            self,
            "选择原生录像核心",
            str(self._replay_settings.core_path or application_root()),
            "录像核心 (myautoplayer-native-replay.exe);;Windows 程序 (*.exe)",
        )
        if not selected:
            return
        path = Path(selected).resolve()
        if path.name.casefold() != "myautoplayer-native-replay.exe":
            QMessageBox.warning(
                self, "录像核心无效", "请选择 myautoplayer-native-replay.exe"
            )
            return
        self._replay_settings = self._replay_settings_store.save(
            ReplaySettings(
                self._replay_settings.save_directory,
                self._replay_settings.duration_minutes,
                self._replay_settings.quality,
                self._replay_settings.encoder_mode,
                self._replay_settings.fps,
                self._replay_settings.monitor_index,
                path,
                self._replay_settings.record_microphone,
                self._replay_settings.microphone_device_id,
                self._replay_settings.microphone_device_name,
                self._replay_settings.microphone_gain_percent,
            )
        )
        self._refresh_replay_core_status()
        self._schedule_audio_preview_restart()

    def _auto_detect_replay_core(self) -> None:
        self._replay_settings = self._replay_settings_store.save(
            ReplaySettings(
                self._replay_settings.save_directory,
                self._replay_settings.duration_minutes,
                self._replay_settings.quality,
                self._replay_settings.encoder_mode,
                self._replay_settings.fps,
                self._replay_settings.monitor_index,
                None,
                self._replay_settings.record_microphone,
                self._replay_settings.microphone_device_id,
                self._replay_settings.microphone_device_name,
                self._replay_settings.microphone_gain_percent,
            )
        )
        self._refresh_replay_core_status()
        self._schedule_audio_preview_restart()

    def _refresh_replay_core_status(self) -> None:
        core = self._native_replay_controller.executable_for(self._replay_settings)
        if core is None:
            self._replay_core_path.setText("未找到录像核心")
            self._native_replay_status.setText(
                "尚未找到录像核心。请点击“选择录像核心”。"
            )
            self._start_native_replay_button.setEnabled(False)
            return
        self._replay_core_path.setText(str(core))
        self._native_replay_status.setText(
            f"录像核心已就绪：{core}。将录制所选显示器的全局画面和全局物理按键。"
        )
        self._start_native_replay_button.setEnabled(True)

    def _choose_replay_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "选择视频保存目录",
            str(self._replay_settings.save_directory),
        )
        if not selected:
            return
        self._replay_save_directory.setText(selected)
        self._save_replay_settings()

    def _open_replay_directory(self) -> None:
        folder = self._replay_settings.save_directory
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.warning(self, "无法打开视频保存目录", str(exc))
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve()))):
            QMessageBox.warning(self, "无法打开视频保存目录", str(folder.resolve()))

    def _refresh_replay_history(self) -> None:
        selected = self._selected_replay_history_entry()
        selected_path = selected.directory if selected is not None else None
        self._replay_history_store = ReplayHistoryStore(
            self._replay_settings.save_directory
        )
        self._replay_history_entries = self._replay_history_store.scan()
        table = self._replay_history_table
        table.setRowCount(len(self._replay_history_entries))
        selected_row = -1
        for row, entry in enumerate(self._replay_history_entries):
            values = (
                entry.saved_at_text,
                entry.display_name,
                entry.duration_text,
                entry.video_format_text,
                entry.encoder,
                entry.audio_text,
                entry.status,
            )
            tooltip = (
                f"会话目录：{entry.directory}\n"
                f"按键事件：{entry.event_count if entry.event_count is not None else '未知'} 条"
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(tooltip)
                table.setItem(row, column, item)
            if selected_path is not None and entry.directory == selected_path:
                selected_row = row
        if selected_row >= 0:
            table.selectRow(selected_row)
        else:
            table.clearSelection()
        count = len(self._replay_history_entries)
        self._replay_history_summary.setText(
            f"当前保存地址共找到 {count} 个录像会话，最新记录排在最上方。"
            if count
            else "当前保存地址还没有录像会话；点击“保留过往”成功后会自动出现在这里。"
        )
        self._update_replay_history_actions()

    def _selected_replay_history_entry(self) -> ReplayHistoryEntry | None:
        table = getattr(self, "_replay_history_table", None)
        entries = getattr(self, "_replay_history_entries", ())
        if table is None:
            return None
        rows = table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        return entries[row] if 0 <= row < len(entries) else None

    def _update_replay_history_actions(self) -> None:
        entry = self._selected_replay_history_entry()
        self._play_replay_history_button.setEnabled(
            entry is not None and entry.raw_video.is_file()
        )
        self._open_replay_subtitle_button.setEnabled(
            entry is not None and entry.subtitle_path is not None
        )
        self._open_replay_session_button.setEnabled(entry is not None)
        self._delete_replay_history_button.setEnabled(entry is not None)

    @staticmethod
    def _open_history_path(path: Path, title: str, parent: QWidget) -> None:
        if not path.exists():
            QMessageBox.warning(parent, title, f"文件或目录已经不存在：\n{path}")
            return
        try:
            resolved = path.resolve()
        except OSError as exc:
            QMessageBox.warning(parent, title, str(exc))
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(resolved))):
            QMessageBox.warning(parent, title, f"Windows 无法打开：\n{resolved}")

    def _play_selected_replay_history(self) -> None:
        entry = self._selected_replay_history_entry()
        if entry is not None:
            self._open_history_path(entry.raw_video, "无法播放原始视频", self)

    def _open_selected_replay_subtitle(self) -> None:
        entry = self._selected_replay_history_entry()
        if entry is None:
            return
        subtitle = entry.subtitle_path
        if subtitle is None:
            QMessageBox.warning(self, "无法打开外挂字幕", "所选会话没有 ASS 或 SRT 字幕")
            return
        self._open_history_path(subtitle, "无法打开外挂字幕", self)

    def _open_selected_replay_directory(self) -> None:
        entry = self._selected_replay_history_entry()
        if entry is not None:
            self._open_history_path(entry.directory, "无法打开会话目录", self)

    def _delete_selected_replay_history(self) -> None:
        entry = self._selected_replay_history_entry()
        if entry is None:
            return
        answer = QMessageBox.question(
            self,
            "确认删除录像会话",
            f"确定将下面这个完整录像会话移入 Windows 回收站吗？\n\n"
            f"{entry.directory.name}\n\n"
            "原始视频、外挂字幕、按键日志和元数据会一起移动。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._replay_history_store.move_to_recycle_bin(entry)
        except ReplayHistoryError as exc:
            QMessageBox.warning(self, "删除录像会话失败", str(exc))
            return
        self._refresh_replay_history()

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
        self._osd_size_field = RoseSpinBox()
        self._osd_size_field.setObjectName("osd_size_field")
        self._osd_size_field.setRange(10, 72)
        self._osd_size_field.setSuffix(" px")
        self._osd_size_field.setValue(self._osd_popup.popup_size)
        self._osd_size_field.valueChanged.connect(self._osd_popup.set_size)
        layout.addRow("OSD 文字大小", self._osd_size_field)
        self._osd_background_field = QCheckBox("显示淡色半透明背景")
        self._osd_background_field.setObjectName("osd_background_field")
        self._osd_background_field.setChecked(
            self._osd_popup.popup_background_enabled
        )
        self._osd_background_field.toggled.connect(
            self._osd_popup.set_background_enabled
        )
        layout.addRow("OSD 背景", self._osd_background_field)
        self._sound_enabled_field = QCheckBox("启用提示音（默认开启）")
        self._sound_enabled_field.setChecked(self._sound_effects.enabled)
        self._sound_enabled_field.toggled.connect(self._sound_effects.set_enabled)
        layout.addRow("提示音", self._sound_enabled_field)
        self._clear_logs_button = QPushButton("删除过往日志")
        self._clear_logs_button.setObjectName("clear_historical_logs_button")
        self._clear_logs_button.setToolTip("可选择清理 30 天、5 天或 1 天以前的日志；今天日志不会删除")
        self._open_logs_button = QPushButton("打开日志文件夹")
        self._open_logs_button.setObjectName("open_logs_folder_button")
        self._open_logs_button.setToolTip("在资源管理器中浏览并手动管理日志")
        log_actions = QWidget()
        log_actions_layout = QHBoxLayout(log_actions)
        log_actions_layout.setContentsMargins(0, 0, 0, 0)
        log_actions_layout.addWidget(self._clear_logs_button)
        log_actions_layout.addWidget(self._open_logs_button)
        layout.addRow("日志管理", log_actions)
        info = QLabel(_INSTRUCTION_TEXT)
        info.setWordWrap(True)
        layout.addRow("使用说明", info)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        self._clear_logs_button.clicked.connect(self._clear_historical_logs)
        self._open_logs_button.clicked.connect(self._open_log_folder)
        return page

    def _clear_historical_logs(self) -> None:
        choices = {
            "删除超过一个月的日志（30 天前及更早）": 30,
            "删除超过 5 天的日志（5 天前及更早）": 5,
            "删除超过 1 天的日志（只保留今天）": 1,
        }
        selected, accepted = QInputDialog.getItem(
            self,
            "选择日志清理范围",
            "今天的日志始终保留，请选择：",
            list(choices),
            0,
            False,
        )
        if not accepted:
            return
        retention_days = choices[selected]
        answer = QMessageBox.question(
            self,
            "删除过往日志",
            f"确定执行“{selected}”吗？\n今天正在使用的日志不会删除。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            removed = clear_logs_older_than(retention_days)
        except OSError as exc:
            QMessageBox.warning(self, "日志清理失败", str(exc))
            return
        QMessageBox.information(
            self,
            "日志清理完成",
            f"已删除 {removed} 个历史日志文件。\n今天的日志仍然保留。",
        )

    def _open_log_folder(self) -> None:
        folder = log_root()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.warning(self, "无法打开日志文件夹", str(exc))
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve()))):
            QMessageBox.warning(self, "无法打开日志文件夹", str(folder.resolve()))

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
        if getattr(self, "_key_monitor_window", None) is not None:
            monitor = self._key_monitor_window
            if self._hotkey_mgr:
                self._hotkey_mgr.remove_physical_observer(monitor.observe_input)
            monitor.close()
            self._key_monitor_window = None
        if getattr(self, "_native_replay_timer", None):
            self._native_replay_timer.stop()
        if getattr(self, "_audio_preview_restart_timer", None):
            self._audio_preview_restart_timer.stop()
        if getattr(self, "_audio_preview_controller", None):
            self._audio_preview_controller.stop()
        if getattr(self, "_native_replay_controller", None):
            if self._hotkey_mgr:
                self._hotkey_mgr.remove_physical_observer(
                    self._native_replay_controller.observe_input
                )
            self._native_replay_controller.stop()
            self._native_replay_controller.cleanup_buffer()
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


def install_chinese_qt_translator(app: QApplication) -> bool:
    """统一翻译 Qt 标准弹窗按钮，例如 OK/Cancel/Yes/No。"""
    translator = QTranslator(app)
    translations = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    loaded = translator.load("qt_zh_CN", translations) or translator.load(
        "qtbase_zh_CN", translations
    )
    if not loaded:
        logger.warning("未找到 Qt 简体中文翻译文件：%s", translations)
        return False
    app.installTranslator(translator)
    app._myautoplayer_chinese_translator = translator
    return True


def show_startup_window(window: QMainWindow) -> None:
    """首次/重复启动时先保证可见，再尝试取得键盘前台焦点。"""
    window.show()
    _activate_startup_window(window)
    QTimer.singleShot(0, lambda: _activate_startup_window(window))
    QTimer.singleShot(160, lambda: _activate_startup_window(window))
    QTimer.singleShot(900, lambda: _release_startup_topmost(window))


def _activate_startup_window(window: QMainWindow) -> None:
    try:
        window.raise_()
        window.activateWindow()
    except RuntimeError:
        return
    if sys.platform != "win32" or not hasattr(window, "winId"):
        return
    try:
        hwnd = int(window.winId())
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
        user32.ShowWindow.restype = wintypes.BOOL
        user32.SetWindowPos.argtypes = (
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        )
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.argtypes = (
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        )
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.AttachThreadInput.argtypes = (
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.BOOL,
        )
        user32.AttachThreadInput.restype = wintypes.BOOL
        user32.BringWindowToTop.argtypes = (wintypes.HWND,)
        user32.BringWindowToTop.restype = wintypes.BOOL
        user32.SetActiveWindow.argtypes = (wintypes.HWND,)
        user32.SetActiveWindow.restype = wintypes.HWND
        user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
        user32.SetForegroundWindow.restype = wintypes.BOOL
        kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        flags = 0x0001 | 0x0002 | 0x0040  # NOSIZE | NOMOVE | SHOWWINDOW
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, flags)  # HWND_TOPMOST
        foreground = user32.GetForegroundWindow()
        current_thread = kernel32.GetCurrentThreadId()
        foreground_thread = (
            user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
        )
        attached = False
        if foreground_thread and foreground_thread != current_thread:
            attached = bool(
                user32.AttachThreadInput(current_thread, foreground_thread, True)
            )
        try:
            user32.BringWindowToTop(hwnd)
            user32.SetActiveWindow(hwnd)
            focused = bool(user32.SetForegroundWindow(hwnd))
            if not focused:
                logger.info("Windows 暂未授予启动前台焦点；窗口已临时置顶保证可见")
        finally:
            if attached:
                user32.AttachThreadInput(current_thread, foreground_thread, False)
    except (AttributeError, OSError, RuntimeError, TypeError):
        pass


def _release_startup_topmost(window: QMainWindow) -> None:
    """结束短暂置顶，不改变用户之后的普通窗口层级。"""
    if sys.platform != "win32" or not hasattr(window, "winId"):
        return
    try:
        hwnd = int(window.winId())
        flags = 0x0001 | 0x0002 | 0x0010  # NOSIZE | NOMOVE | NOACTIVATE
        ctypes.windll.user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, flags)
    except (AttributeError, OSError, RuntimeError, TypeError):
        pass


def main() -> int:
    startup_started = _IMPORT_STARTED_AT
    _enable_per_monitor_v2_dpi()
    _set_windows_app_identity()
    instance = SingleInstanceGuard()
    if not instance.acquire():
        return 0
    try:
        setup_logging()
        logger.info("自动连招启动")
        macro_runtime = PythonMacroRuntime()
        app = QApplication(sys.argv)
        install_chinese_qt_translator(app)
        qt_ready = time.perf_counter()
        app.setApplicationName(_APP_TITLE)
        app.setWindowIcon(application_icon())
        if not _is_admin():
            logger.warning("当前未以管理员权限运行，某些游戏可能无法接收模拟输入")
        window = MainWindow(macro_runtime)
        window_ready = time.perf_counter()
        show_startup_window(window)
        activation_timer = QTimer(window)
        activation_timer.setInterval(100)
        activation_timer.timeout.connect(
            lambda: show_startup_window(window)
            if instance.consume_activation_request()
            else None
        )
        activation_timer.start()
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
