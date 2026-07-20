"""C1 宏库只读页面、静态检测和文件监听。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QRegularExpression, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from src.core.macro_file_manager import MacroFileError, MacroFileManager
from src.core.macro_library import MacroEntry, scan_macro_root
from src.ui.ai_prompt_dialog import AiPromptDialog, build_ai_prompt_content
from src.ui.table_selection import PreserveForegroundSelectionDelegate


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """仅负责可读性，不校验、导入或执行用户 Python 代码。"""

    def __init__(self, document):
        super().__init__(document)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._add_rule(
            r"\b(?:and|as|assert|async|await|break|class|continue|def|del|elif|else|"
            r"except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|"
            r"pass|raise|return|try|while|with|yield)\b",
            "#B00070",
        )
        self._add_rule(r"\b(?:True|False|None)\b", "#7A3E9D")
        self._add_rule(r"\b\d+(?:\.\d+)?\b", "#005F8B")
        self._add_rule(r"@[A-Za-z_]\w*", "#7A3E9D")
        self._add_rule(r"\bdef\s+[A-Za-z_]\w*", "#005F8B")
        self._add_rule(r"(?:\"(?:\\\\.|[^\"\\\\])*\"|'(?:\\\\.|[^'\\\\])*')", "#A04A00")
        self._add_rule(r"#.*$", "#5F6B5F")

    def _add_rule(self, pattern: str, color: str) -> None:
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        self._rules.append((QRegularExpression(pattern), text_format))

    def highlightBlock(self, text: str) -> None:  # noqa: N802 - Qt callback name
        for expression, text_format in self._rules:
            match = expression.globalMatch(text)
            while match.hasNext():
                current = match.next()
                self.setFormat(current.capturedStart(), current.capturedLength(), text_format)


class PythonCodeEditor(QPlainTextEdit):
    """受控 Python 编辑区：提供四空格 Tab 与最小 Python 自动缩进。"""

    _INDENT = "    "

    def __init__(self, source: str, parent: QWidget | None = None):
        super().__init__(source, parent)
        self.setTabStopDistance(32)
        self.highlighter = PythonSyntaxHighlighter(self.document())

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt callback name
        cursor = self.textCursor()
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and self._can_auto_indent(cursor):
            line_before_cursor = cursor.block().text()[: cursor.positionInBlock()]
            indentation = line_before_cursor[: len(line_before_cursor) - len(line_before_cursor.lstrip(" \t"))]
            code_before_cursor = line_before_cursor.strip()
            if code_before_cursor and not code_before_cursor.startswith("#") and code_before_cursor.endswith(":"):
                indentation += self._INDENT
            cursor.insertText("\n" + indentation)
            event.accept()
            return
        if event.key() == Qt.Key.Key_Tab:
            if cursor.hasSelection():
                selected = cursor.selectedText().replace("\u2029", "\n")
                cursor.insertText(self._INDENT + selected.replace("\n", "\n" + self._INDENT))
            else:
                cursor.insertText(self._INDENT)
            event.accept()
            return
        super().keyPressEvent(event)

    @staticmethod
    def _can_auto_indent(cursor) -> bool:
        return not cursor.hasSelection() and cursor.atBlockEnd()


class MacroEditorDialog(QDialog):
    """内置 Python 宏编辑器；保存工作仍交给受控文件服务。"""

    def __init__(self, parent: QWidget, title: str, name: str, source: str, on_save):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(620, 460)
        self._on_save = on_save
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Python 宏名称"))
        self.name_field = QLineEdit(name)
        self.name_field.setObjectName("macro_editor_name_field")
        layout.addWidget(self.name_field)
        self.source_editor = PythonCodeEditor(source)
        self.source_editor.setObjectName("macro_source_editor")
        layout.addWidget(self.source_editor, 1)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @Slot()
    def _save(self) -> None:
        try:
            self._on_save(self.name_field.text(), self.source_editor.toPlainText())
        except MacroFileError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        self.accept()


class MacroLibraryPanel(QWidget):
    """显示受控宏目录；只发出状态请求，绝不加载或执行宏。"""

    entries_changed = Signal(object)
    active_path_renamed = Signal(object, object)

    def __init__(
        self,
        root: Path,
        parent: QWidget | None = None,
        prompt_config_dir: Path | None = None,
        on_delete_requested=None,
    ):
        super().__init__(parent)
        self._root = root
        self._prompt_config_dir = prompt_config_dir
        self._on_delete_requested = on_delete_requested
        self._manager = MacroFileManager(root)
        self._entries: list[MacroEntry] = []
        self._active_path: Path | None = None
        self._ai_prompt_dialog: AiPromptDialog | None = None
        self._build_ui()
        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._schedule_refresh)
        self._watcher.fileChanged.connect(self._schedule_refresh)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(150)
        self._refresh_timer.timeout.connect(self.refresh)
        self.refresh()

    @property
    def entries(self) -> list[MacroEntry]:
        return self._entries

    @property
    def refresh_timer(self) -> QTimer:
        return self._refresh_timer

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        self.table = QTableWidget(0, 2)
        self.table.setObjectName("macro_library_table")
        self.table.setHorizontalHeaderLabels(["序号", "Python 宏"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setItemDelegate(PreserveForegroundSelectionDelegate(self.table))
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 52)
        self.table.itemSelectionChanged.connect(self._show_selected_detail)
        self.table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table, 1)

        action_panel = QWidget()
        action_panel.setObjectName("macro_action_panel")
        action_panel.setFixedWidth(176)
        actions = QVBoxLayout(action_panel)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(10)
        self._name_field = QLineEdit()
        self._name_field.setObjectName("macro_name_field")
        self._name_field.setPlaceholderText("未选择")
        self._name_field.returnPressed.connect(self._rename_selected_macro)
        actions.addWidget(self._name_field)
        self._new_button = QPushButton("新建")
        self._new_button.clicked.connect(self._create_macro)
        actions.addWidget(self._new_button)
        self._edit_button = QPushButton("编辑")
        self._edit_button.clicked.connect(self._edit_selected_macro)
        actions.addWidget(self._edit_button)
        self._ai_prompt_button = QPushButton("AI 提示词")
        self._ai_prompt_button.setObjectName("ai_prompt_button")
        self._ai_prompt_button.clicked.connect(self._open_ai_prompt_dialog)
        actions.addWidget(self._ai_prompt_button)
        self._save_button = QPushButton("保存")
        self._save_button.setToolTip("保存右侧名称修改")
        self._save_button.clicked.connect(self._rename_selected_macro)
        actions.addWidget(self._save_button)
        self._reload_button = QPushButton("重新加载")
        self._reload_button.clicked.connect(self.refresh)
        actions.addWidget(self._reload_button)
        self._delete_button = QPushButton("删除")
        self._delete_button.clicked.connect(self._delete_selected_macro)
        self._delete_button.setToolTip("移入 Windows 回收站")
        actions.addWidget(self._delete_button)
        actions.addStretch()
        layout.addWidget(action_panel)

    @staticmethod
    def _readonly_field(value: str) -> QLineEdit:
        field = QLineEdit(value)
        field.setReadOnly(True)
        field.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return field

    def refresh(self) -> None:
        selected_path = self._selected_path()
        self._entries = scan_macro_root(self._root)
        self._rebuild_watches()
        self._render(selected_path)
        self.entries_changed.emit(self._entries)

    def set_active_path(self, path: Path | None) -> None:
        self._active_path = path
        self._update_action_state()

    def update_trigger_settings(
        self,
        path: Path,
        *,
        hotkey: str,
        mode: str,
        count: int,
        speed: float,
        enabled: bool,
    ) -> None:
        """触发页的每一次有效编辑均即时原子保存并刷新。"""
        self._manager.update_trigger_settings(
            path,
            hotkey=hotkey,
            mode=mode,
            count=count,
            speed=speed,
            enabled=enabled,
        )
        self._refresh_and_select(path)

    @Slot(str)
    def _schedule_refresh(self, _changed_path: str) -> None:
        self._refresh_timer.start()

    def _rebuild_watches(self) -> None:
        watched = self._watcher.directories() + self._watcher.files()
        if watched:
            self._watcher.removePaths(watched)
        paths = [str(self._root)] if self._root.is_dir() else []
        paths.extend(str(entry.path) for entry in self._entries if entry.path.is_file())
        if paths:
            self._watcher.addPaths(paths)

    def _render(self, selected_path: Path | None) -> None:
        self.table.setRowCount(len(self._entries))
        selected_row = None
        for row, entry in enumerate(self._entries):
            values = (str(row + 1), entry.path.stem)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if column == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if not entry.valid and column == 1:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, column, item)
            if entry.path == selected_path:
                selected_row = row
        if selected_row is not None:
            self.table.selectRow(selected_row)
        else:
            self.table.clearSelection()
        self._show_selected_detail()

    @Slot()
    def _show_selected_detail(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._name_field.clear()
            self._update_action_state()
            return
        entry = self._entries[rows[0].row()]
        self._name_field.setText(entry.macro.name if entry.macro else entry.path.stem)
        self._update_action_state()

    @Slot(int, int)
    def _on_cell_clicked(self, row: int, column: int) -> None:
        self.table.selectRow(row)

    def _selected_entry(self) -> MacroEntry | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows or rows[0].row() >= len(self._entries):
            return None
        return self._entries[rows[0].row()]

    def _selected_path(self) -> Path | None:
        entry = self._selected_entry()
        return entry.path if entry is not None else None

    def _update_action_state(self) -> None:
        entry = self._selected_entry()
        editable = entry is not None and entry.valid
        self._name_field.setEnabled(editable)
        self._edit_button.setEnabled(editable)
        self._save_button.setEnabled(editable)
        self._delete_button.setEnabled(entry is not None)
        self._name_field.setToolTip("")

    @Slot()
    def _create_macro(self) -> None:
        dialog = MacroEditorDialog(
            self,
            "新建 Python 宏",
            "新宏",
            self._manager.template_source("新宏"),
            self._save_new_macro,
        )
        dialog.exec()

    def _save_new_macro(self, name: str, source: str) -> None:
        target = self._manager.create(name, source)
        self._refresh_and_select(target)

    @Slot()
    def _edit_selected_macro(self) -> None:
        entry = self._editable_selected_entry()
        if entry is None:
            return
        try:
            source = self._manager.read_source(entry.path)
        except MacroFileError as exc:
            QMessageBox.warning(self, "无法编辑", str(exc))
            return
        dialog = MacroEditorDialog(
            self,
            f"编辑 Python 宏：{entry.path.name}",
            self._name_field.text(),
            source,
            lambda name, edited_source: self._save_existing_macro(
                entry.path, name, edited_source
            ),
        )
        dialog.exec()

    @Slot()
    def _open_ai_prompt_dialog(self) -> None:
        content = self._build_ai_prompt_content()
        dialog = self._ai_prompt_dialog
        if dialog is None:
            dialog = AiPromptDialog(self, content.text, content.load)
            dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            dialog.destroyed.connect(lambda *_: setattr(self, "_ai_prompt_dialog", None))
            self._ai_prompt_dialog = dialog
        else:
            dialog.update_prompt(content.text, content.load)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _build_ai_prompt(self) -> str:
        return self._build_ai_prompt_content().text

    def _build_ai_prompt_content(self):
        entry = self._selected_entry()
        if entry is None or not entry.valid:
            return build_ai_prompt_content(config_dir=self._prompt_config_dir)
        try:
            source = self._manager.read_source(entry.path)
        except MacroFileError:
            return build_ai_prompt_content(config_dir=self._prompt_config_dir)
        return build_ai_prompt_content(source, config_dir=self._prompt_config_dir)

    @Slot()
    def _rename_selected_macro(self) -> None:
        entry = self._editable_selected_entry()
        if entry is None:
            return
        try:
            target = self._manager.rename(entry.path, self._name_field.text())
        except MacroFileError as exc:
            QMessageBox.warning(self, "重命名失败", str(exc))
            return
        self._sync_active_rename(entry.path, target)
        self._refresh_and_select(target)

    def _save_existing_macro(self, path: Path, name: str, source: str) -> None:
        target = self._manager.update(
            path, name, source
        )
        self._sync_active_rename(path, target)
        self._refresh_and_select(target)

    def _editable_selected_entry(self) -> MacroEntry | None:
        entry = self._selected_entry()
        if entry is None or not entry.valid:
            return None
        return entry

    @Slot()
    def _delete_selected_macro(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        if not self._confirm_delete(entry.path.name):
            return
        if self._on_delete_requested is not None:
            self._on_delete_requested(entry.path)

    def _confirm_delete(self, filename: str) -> bool:
        """使用固定中文按钮；默认取消，避免依赖 Qt 的系统语言。"""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("确认删除")
        dialog.setText(f"确定将“{filename}”移入 Windows 回收站吗？")
        confirm = dialog.addButton("确认删除", QMessageBox.ButtonRole.AcceptRole)
        cancel = dialog.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        dialog.setDefaultButton(cancel)
        dialog.exec()
        return dialog.clickedButton() is confirm

    def delete_path_after_stop(self, path: Path) -> None:
        """仅由主窗口在停止并清空活动状态后调用。"""
        self._manager.move_to_recycle_bin(path)
        self._refresh_and_select(None)

    def _sync_active_rename(self, previous: Path, target: Path) -> None:
        if self._active_path is not None and previous == self._active_path and target != previous:
            self._active_path = target
            self.active_path_renamed.emit(previous, target)

    def _refresh_and_select(self, path: Path | None) -> None:
        self._entries = scan_macro_root(self._root)
        self._rebuild_watches()
        self._render(path)
        self.entries_changed.emit(self._entries)
