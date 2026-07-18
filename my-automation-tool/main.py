"""MyAutoPlayer 程序入口：阶段 3 的单 Python 键盘测试宏。"""
from __future__ import annotations

import atexit
import ctypes
import sys
from pathlib import Path

import keyboard
from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
from src.core.sequence_player import SequencePlayer
from src.core.script_engine import (
    PythonMacroRuntime,
    PythonMacroValidationError,
    run_python_macro_once,
)
from src.core.macro_library import MacroEntry, MacroMetadata
from src.ui.macro_library_panel import MacroLibraryPanel
from src.ui.game_keybinds_panel import GameKeybindsPanel
from src.ui.osd_window import OsdPopup
from src.ui.window_chrome import (
    VerticalResizeHandle,
    WindowChromeController,
    WindowTitleBar,
    application_icon,
)
from src.utils.app_paths import macro_root
from src.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)
_MACRO_ROOT = macro_root()
_APP_TITLE = "自动连招"
_WINDOWS_APP_ID = "ssc8537.MyAutoPlayer"
_INSTRUCTION_TEXT = (
    "自动连招已启动\n\n按 F12 启用/禁用热键\n"
    "先在宏库启用一个 Python 宏，再轻按 F9 运行\n"
    "（鼠标不要在程序窗口内）"
)


def global_status_notification(disabled: bool) -> tuple[str, bool]:
    """返回全局开关 OSD 的文本和颜色状态。"""
    if disabled:
        return "全局脚本已禁用", False
    return "全局脚本已就绪", True


class _HotkeyDispatcher(QObject):
    """在 Qt 主线程协调热键、OSD 和后台序列播放器。"""

    f9_signal = Signal()
    f9_stop_signal = Signal()
    toggle_signal = Signal(bool)
    player_finished_signal = Signal()

    macro_error_signal = Signal(str)

    def __init__(
        self,
        status_label: QLabel,
        osd_popup: OsdPopup,
        macro_runtime: PythonMacroRuntime,
    ):
        super().__init__()
        self._status_label = status_label
        self._osd_popup = osd_popup
        self._macro_runtime = macro_runtime
        self._player = SequencePlayer(on_finished=self._on_player_finished_worker)
        self._on_natural_finish = None
        self._on_binding_configuration = None
        self._execution_active = False
        self._running_macro_name: str | None = None
        self.f9_signal.connect(self._start_f9, Qt.ConnectionType.QueuedConnection)
        self.f9_stop_signal.connect(self._stop_f9, Qt.ConnectionType.QueuedConnection)
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

    def on_f9_hook(self) -> None:
        """由钩子线程重载已保存 Python 宏，再安全转发启动请求。"""
        try:
            if self._macro_runtime.selected_path() is None:
                self.macro_error_signal.emit("未选择有效宏，F9 未启动")
                return
            macro = self._macro_runtime.reload()
            if self._on_binding_configuration is not None:
                self._on_binding_configuration(macro)
        except PythonMacroValidationError as exc:
            logger.warning("F9 未启动：Python 宏无效：%s", exc)
            if self._on_natural_finish is not None:
                self._on_natural_finish()
            self.macro_error_signal.emit("Python 宏无效，未启动")
            return
        self.f9_signal.emit()

    def on_f9_stop_hook(self) -> None:
        """仅由 keyboard 钩子线程调用。"""
        self.f9_stop_signal.emit()

    def on_toggle_hook(self, disabled: bool) -> None:
        """仅由 keyboard 钩子线程调用。"""
        self.toggle_signal.emit(disabled)

    def _on_player_finished_worker(self) -> None:
        """播放器线程仅转发信号，绝不直接触碰 Qt 控件。"""
        self.player_finished_signal.emit()

    @Slot()
    def _start_f9(self) -> None:
        macro = self._macro_runtime.current()
        if macro is None:
            return
        if not self._player.play(
            lambda stop_event: run_python_macro_once(macro, stop_event), macro.count
        ):
            logger.info("F9 启动被忽略：Python 宏已经运行")
            return
        self._execution_active = True
        self._running_macro_name = macro.name
        logger.info("F9 启动 Python 宏：%s，count=%s", macro.name, macro.count)
        self._osd_popup.show_notification(f"{macro.name} 宏运行中", success=True)

    @Slot()
    def _stop_f9(self) -> None:
        self._player.stop()
        if not self._execution_active:
            return
        self._execution_active = False
        name = self._running_macro_name or "当前宏"
        self._running_macro_name = None
        logger.info("F9 松开/全局禁用 — Python 宏停止：%s", name)
        self._osd_popup.show_notification(f"{name} 宏已停止", success=False)

    @Slot()
    def _on_player_finished(self) -> None:
        if self._on_natural_finish is not None:
            self._on_natural_finish()
        if self._execution_active:
            self._execution_active = False
            name = self._running_macro_name or "当前宏"
            self._running_macro_name = None
            logger.info("Python 宏自然结束：%s", name)
            self._osd_popup.show_notification(f"{name} 宏已停止", success=False)

    @Slot(str)
    def _show_macro_error(self, message: str) -> None:
        self._osd_popup.show_notification(message, success=False)

    def stop_active_execution(self) -> None:
        self._player.stop()
        self._player.join(timeout=1.0)

    @Slot(bool)
    def _apply_global_status(self, disabled: bool) -> None:
        notification, success = global_status_notification(disabled)
        if disabled:
            self._status_label.setText("🔴 热键已禁用")
            self._status_label.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
        else:
            self._status_label.setText("🟢 热键已启用")
            self._status_label.setStyleSheet("font-size: 20px; color: green; font-weight: bold;")
        self._osd_popup.show_notification(notification, success=success)


class MainWindow(QMainWindow):
    """阶段 3 运行入口和 v021 只读四页 UI 外壳。"""

    def __init__(self, macro_runtime: PythonMacroRuntime):
        super().__init__()
        self.setWindowTitle(_APP_TITLE)
        self._macro_runtime = macro_runtime
        self._hotkey_mgr: HotkeyManager | None = None
        self._macro_entries: list[MacroEntry] = []
        self._active_macro_path: Path | None = None
        self._setup_ui()
        self._osd_popup = OsdPopup(None)
        self._dispatcher = _HotkeyDispatcher(
            self._status_label, self._osd_popup, macro_runtime
        )
        self._setup_hotkey()

    def _setup_ui(self) -> None:
        if not hasattr(self, "_macro_entries"):
            self._macro_entries = []
        if not hasattr(self, "_active_macro_path"):
            self._active_macro_path = None
        self.setFixedWidth(642)
        self.setWindowIcon(application_icon())
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setMinimumHeight(510)
        screen = QApplication.primaryScreen()
        if screen is not None:
            self.setMaximumHeight(screen.availableGeometry().height())
        self.resize(642, 510)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._title_bar = WindowTitleBar(central_widget)
        self._window_chrome = WindowChromeController(self)
        layout.addWidget(self._title_bar)

        tabs = QTabWidget()
        tabs.setObjectName("main_tabs")
        tabs.setDocumentMode(True)
        tabs.setUsesScrollButtons(False)
        tabs.addTab(self._build_macro_page(), "宏库")
        tabs.addTab(self._build_trigger_page(), "触发")
        tabs.addTab(self._build_features_page(), "功能")
        tabs.addTab(self._build_settings_page(), "设置")
        layout.addWidget(tabs, 1)
        self._vertical_resize_handle = VerticalResizeHandle(self)
        layout.addWidget(self._vertical_resize_handle)
        self._tabs = tabs
        self._window_chrome.install(self._title_bar)
        self._on_macro_entries_changed(self._macro_panel.entries)
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #FDF; color: black; font-family: "Microsoft YaHei"; font-size: 12px; }
            QWidget#window_title_bar { background: #FCE; border: 1px solid #D8A7C7; }
            QLabel#window_title_label { color: #7A1E4C; font-size: 15px; font-weight: bold; }
            QToolButton#window_hide_button, QToolButton#window_minimize_button, QToolButton#window_close_button { border: 1px solid #D8A7C7; border-radius: 13px; color: #5D294B; font-weight: bold; }
            QToolButton#window_hide_button { background: #F6C5D9; }
            QToolButton#window_minimize_button { background: #F8B8D0; }
            QToolButton#window_close_button { background: #E98AAA; color: white; }
            QToolButton#window_hide_button:hover, QToolButton#window_minimize_button:hover, QToolButton#window_close_button:hover { background: #D96C98; color: white; }
            QWidget#vertical_resize_handle { background: #FCE; border-top: 1px solid #D8A7C7; }
            QTabWidget::pane { border: 1px solid #D8A7C7; border-top: none; }
            QTabBar::tab { background: #FCE; min-width: 160px; max-width: 160px; height: 40px; padding: 0; color: #5D294B; font-size: 17px; font-weight: bold; }
            QTabBar::tab:hover { background: #FBE; }
            QTabBar::tab:selected { background: #FDF; color: #9B2860; }
            QGroupBox { background: #FFF5FF; border: 1px solid #D8A7C7; margin-top: 10px; padding: 10px 8px 8px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QLineEdit, QComboBox { background: #FFF5FF; border: 1px solid #D8A7C7; padding: 4px; min-height: 22px; }
            QTableWidget { background: #FFF; alternate-background-color: #FFF5FF; border: 1px solid #D8A7C7; gridline-color: #F0CDE0; selection-background-color: #FCE; selection-color: #5D294B; }
            QHeaderView::section { background: #FFF0FF; border: none; border-bottom: 1px solid #D8A7C7; padding: 6px; color: #5D294B; font-weight: bold; }
            QPushButton { background: #FCE; border: 1px solid #D8A7C7; min-height: 26px; padding: 4px 10px; }
            QPushButton:hover:!disabled { background: #FBE; }
            QPushButton:disabled, QCheckBox:disabled, QComboBox:disabled { color: #8F7785; background: #F7EAF1; border-color: #E3CCD9; }
            """
        )
        self._center_on_screen()

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        frame = self.frameGeometry()
        frame.moveCenter(screen.availableGeometry().center())
        self.move(frame.topLeft())

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
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        table.horizontalHeader().setStretchLastSection(True)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 窗口宽度固定，前三列必须为“状态”列保留最小宽度；否则 Qt 会在
        # 选中单元格时自动横向滚动，导致最左侧“名称”列被挤出可见区域。
        table.setColumnWidth(0, 38)
        table.setColumnWidth(1, 116)
        table.setColumnWidth(2, 52)
        table.setColumnWidth(3, 70)
        table.itemSelectionChanged.connect(self._show_selected_trigger_detail)
        table.cellClicked.connect(self._on_trigger_cell_clicked)
        self._trigger_table = table
        layout.addWidget(table, 1)

        detail = QGroupBox("触发详情（只读）")
        # 主窗口为固定宽度；固定右栏才能保证左侧四列表不会被内容建议尺寸挤压。
        detail.setFixedWidth(210)
        form = QFormLayout(detail)
        form.setVerticalSpacing(9)
        form.addRow("热键", self._readonly_field("F9"))
        self._trigger_mode_field = self._readonly_field("未选择有效宏")
        self._trigger_count_field = self._readonly_field("未选择有效宏")
        self._trigger_speed_field = self._readonly_field("未选择有效宏")
        self._trigger_status_field = self._readonly_field("未选择有效宏")
        form.addRow("模式", self._trigger_mode_field)
        form.addRow("次数", self._trigger_count_field)
        form.addRow("速度", self._trigger_speed_field)
        form.addRow("状态", self._trigger_status_field)
        form.addRow(self._disabled_button("保存触发设置"))
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
                mode = "按住" if entry.macro.mode == "down" else "切换"
                enabled = entry.path == self._active_macro_path
                values = (
                    str(row + 1),
                    entry.path.stem,
                    "F9",
                    mode,
                    "启用" if enabled else "禁用",
                )
            else:
                values = (str(row + 1), entry.path.stem, "—", "—", "不可启用")
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 1 and not entry.valid:
                    item.setForeground(Qt.GlobalColor.red)
                if column == 4:
                    item.setForeground(
                        Qt.GlobalColor.green if value == "启用" else Qt.GlobalColor.red
                    )
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
            values = ("—", "—", "—", "不可启用" if entry else "未选择有效宏")
        else:
            assert entry.macro is not None
            mode = "按住" if entry.macro.mode == "down" else "切换"
            values = (
                mode,
                str(entry.macro.count),
                str(entry.macro.speed),
                "启用" if entry.path == self._active_macro_path else "禁用",
            )
        for field, value in zip(
            (
                self._trigger_mode_field,
                self._trigger_count_field,
                self._trigger_speed_field,
                self._trigger_status_field,
            ),
            values,
        ):
            field.setText(value)

    @Slot(int, int)
    def _on_trigger_cell_clicked(self, row: int, column: int) -> None:
        self._reset_trigger_horizontal_scroll()
        if column == 4:
            self._toggle_trigger_activity(row)

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
        if path == self._active_macro_path:
            self._dispatcher.stop_active_execution()
            self._active_macro_path = None
            self._macro_runtime.set_selected_path(None)
            if self._hotkey_mgr is not None:
                self._hotkey_mgr.mark_finished("f9")
            self._macro_panel.set_active_path(None)
            self._render_trigger_rows()
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
        layout = QFormLayout(page)
        layout.setContentsMargins(40, 30, 90, 30)
        layout.setHorizontalSpacing(28)
        layout.setVerticalSpacing(16)
        title = QLabel("功能（后续阶段）")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addRow(title)

        description = QLabel("以下项目仅展示规划方向，当前不会注册热键或执行鼠标输入。")
        description.setStyleSheet("color: #7A5268;")
        description.setWordWrap(True)
        layout.addRow(description)
        enabled = QCheckBox("启用快速鼠标点击（后续阶段）")
        enabled.setEnabled(False)
        layout.addRow("快速连点", enabled)
        layout.addRow("触发按键", self._disabled_combo("F2（仅占位）"))
        layout.addRow("点击模式", self._disabled_combo("单击"))
        layout.addRow("点击间隔", self._readonly_field("后续阶段"))
        layout.addRow("", self._disabled_button("应用功能设置"))
        return page

    @staticmethod
    def _disabled_combo(value: str) -> QComboBox:
        combo = QComboBox()
        combo.addItem(value)
        combo.setEnabled(False)
        return combo

    def _build_settings_page(self) -> QWidget:
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
        self._status_label = QLabel("🔴 热键已禁用")
        self._status_label.setObjectName("global_status_label")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._status_label.setStyleSheet("font-size: 20px; color: red; font-weight: bold;")
        layout.addRow("当前状态", self._status_label)
        layout.addRow("全局开关", self._readonly_field("F12"))
        layout.addRow("F2", self._readonly_field("仅 UI 占位，不注册"))
        layout.addRow("OSD", self._readonly_field("沿用既有红绿提示，不提供样式编辑"))
        layout.addRow("主题", self._readonly_field("Candy 粉红主题（固定）"))
        self._game_keybinds_panel = GameKeybindsPanel()
        layout.addRow("共享游戏键位", self._game_keybinds_panel)
        info = QLabel(_INSTRUCTION_TEXT)
        info.setWordWrap(True)
        layout.addRow("使用说明", info)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        return page

    def _setup_hotkey(self) -> None:
        self._hotkey_mgr = HotkeyManager(int(self.winId()))
        self._hotkey_mgr.register(
            "f9",
            self._dispatcher.on_f9_hook,
            mode=TriggerMode.SWITCH,
            stop_callback=self._dispatcher.on_f9_stop_hook,
            stop_on_release=False,
        )
        self._hotkey_mgr.set_global_disable_key("f12")
        self._hotkey_mgr.on_toggle(self._dispatcher.on_toggle_hook)
        self._dispatcher.set_natural_finish_callback(
            lambda: self._hotkey_mgr.mark_finished("f9")
        )
        self._dispatcher.set_binding_configuration_callback(
            lambda updated: self._hotkey_mgr.update_binding_configuration(
                "f9", TriggerMode[updated.mode.upper()], updated.count == 0
            )
        )
        self._hotkey_mgr.start()
        logger.info("C1 宏库已就绪：F9 等待活动宏，F12=全局启停")

    def closeEvent(self, event) -> None:
        logger.info("程序退出")
        if self._dispatcher:
            self._dispatcher.stop_active_execution()
        keyboard.unhook_all()
        if self._hotkey_mgr:
            self._hotkey_mgr.stop()
        if self._osd_popup:
            self._osd_popup.close()
        super().closeEvent(event)


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


def main() -> int:
    setup_logging()
    logger.info("自动连招启动")
    macro_runtime = PythonMacroRuntime()

    _set_windows_app_identity()
    app = QApplication(sys.argv)
    app.setApplicationName(_APP_TITLE)
    app.setWindowIcon(application_icon())
    if not _is_admin():
        logger.warning("当前未以管理员权限运行，某些游戏可能无法接收模拟输入")
    window = MainWindow(macro_runtime)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
