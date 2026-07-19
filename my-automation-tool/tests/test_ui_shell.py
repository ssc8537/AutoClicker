import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QComboBox,
    QGroupBox,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QStyle,
    QStyleOptionSpinBox,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from src.ui.ai_prompt_dialog import AiPromptDialog, build_ai_prompt_content, load_prompt_template
from src.ui.macro_library_panel import MacroEditorDialog, MacroLibraryPanel
from src.ui.game_keybinds_panel import GameKeybindsPanel
from src.ui.window_chrome import VerticalResizeHandle, WindowTitleBar
from src.core.macro_file_manager import MacroFileError

from main import MainWindow
from src.core.script_engine import PythonMacroRuntime


VALID_MACRO = 'NAME="x"\nHOTKEY="f9"\nMODE="switch"\nCOUNT=1\nSPEED=1\ndef run(player): pass\n'


class UiShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(self.window)
        self.window._setup_ui()

    def tearDown(self):
        self.window.deleteLater()

    def test_window_is_fixed_width_and_vertically_resizable(self):
        self.assertFalse(self.window.windowIcon().isNull())
        self.assertEqual(self.window.width(), 642)
        self.assertEqual(self.window.minimumWidth(), 642)
        self.assertEqual(self.window.maximumWidth(), 642)
        self.assertEqual(self.window.minimumHeight(), 510)
        self.assertGreaterEqual(self.window.maximumHeight(), 510)
        screen = QApplication.primaryScreen()
        self.assertIsNotNone(screen)
        self.assertEqual(
            self.window.frameGeometry().center(), screen.availableGeometry().center()
        )
        self.assertIsNotNone(self.window.findChild(WindowTitleBar, "window_title_bar"))
        self.assertIsNotNone(self.window.findChild(VerticalResizeHandle, "vertical_resize_handle"))

    def test_vertical_resize_handle_changes_only_height(self):
        self.window.show()
        resize_handle = self.window.findChild(VerticalResizeHandle, "vertical_resize_handle")
        original_height = self.window.height()
        original_width = self.window.width()
        QTest.mousePress(resize_handle, Qt.MouseButton.LeftButton, pos=resize_handle.rect().center())
        QTest.mouseMove(resize_handle, resize_handle.rect().center() + QPoint(0, 40))
        QTest.mouseRelease(resize_handle, Qt.MouseButton.LeftButton, pos=resize_handle.rect().center() + QPoint(0, 40))
        self.assertGreater(self.window.height(), original_height)
        self.assertEqual(self.window.width(), original_width)

    def test_four_tabs_default_to_macro_library(self):
        tabs = self.window.findChild(QTabWidget, "main_tabs")
        self.assertIsNotNone(tabs)
        self.assertEqual(tabs.currentIndex(), 0)
        self.assertEqual([tabs.tabText(index) for index in range(tabs.count())], ["宏库", "触发", "功能", "设置"])
        tabs.setCurrentIndex(2)
        self.assertEqual(tabs.currentIndex(), 2)

    def test_trigger_table_prioritizes_name_width_and_short_status(self):
        table = self.window.findChild(QTableWidget, "trigger_table")
        self.assertGreater(table.columnWidth(1), table.columnWidth(2))
        self.assertGreater(table.columnWidth(1), table.columnWidth(4))
        self.assertEqual(table.columnWidth(4), 44)
        titles = {group.title() for group in self.window.findChildren(QGroupBox)}
        self.assertIn("触发详情（自动保存）", titles)

    def test_trigger_spin_box_arrows_are_visible_and_clickable(self):
        self.window.findChild(QTabWidget, "main_tabs").setCurrentIndex(1)
        self.window.show()
        self.app.processEvents()
        field = self.window._trigger_speed_field
        field.setEnabled(True)
        field.setValue(1.0)
        option = QStyleOptionSpinBox()
        field.initStyleOption(option)
        up_rect = field.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox,
            option,
            QStyle.SubControl.SC_SpinBoxUp,
            field,
        )
        down_rect = field.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox,
            option,
            QStyle.SubControl.SC_SpinBoxDown,
            field,
        )
        self.assertFalse(up_rect.isEmpty())
        self.assertFalse(down_rect.isEmpty())
        self.assertEqual(type(field).__name__, "RoseDoubleSpinBox")
        self.assertEqual(field.grab().toImage().pixelColor(up_rect.center()).name(), "#6e4055")
        self.assertEqual(field.grab().toImage().pixelColor(down_rect.center()).name(), "#6e4055")
        QTest.mouseClick(field, Qt.MouseButton.LeftButton, pos=up_rect.center())
        self.assertGreater(field.value(), 1.0)

    def test_clicking_an_unselected_status_cell_toggles_that_row_immediately(self):
        """案例行为：状态列单击以点击行保存，不要求先选中宏。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "first.py").write_text(VALID_MACRO, encoding="utf-8")
            target = root / "second.py"
            target.write_text(
                VALID_MACRO.replace('NAME="x"', 'NAME="second"'), encoding="utf-8"
            )
            manager = Mock()
            with patch("main._MACRO_ROOT", root), patch(
                "main.HotkeyManager", return_value=manager
            ), patch("main.OsdPopup"):
                window = MainWindow(PythonMacroRuntime())
            tabs = window.findChild(QTabWidget, "main_tabs")
            tabs.setCurrentIndex(1)
            window.show()
            self.app.processEvents()
            table = window._trigger_table
            target_row = next(
                row for row, entry in enumerate(window._macro_entries) if entry.path == target
            )
            table.clearSelection()
            self.app.processEvents()

            QTest.mouseClick(
                table.viewport(),
                Qt.MouseButton.LeftButton,
                pos=table.visualItemRect(table.item(target_row, 4)).center(),
            )
            self.app.processEvents()

            self.assertEqual(table.item(target_row, 4).text(), "禁用")
            self.assertIn("ENABLED = False", target.read_text(encoding="utf-8"))
            self.assertEqual(table.selectionModel().selectedRows()[0].row(), target_row)
            window.close()

    @unittest.skip("Stage 6B 触发页从只读控件升级为即时可编辑控件")
    def test_macro_and_trigger_pages_have_only_stage_2b_controls(self):
        buttons = {button.text(): button for button in self.window.findChildren(QPushButton)}
        self.assertTrue(buttons["新建"].isEnabled())
        self.assertTrue(buttons["重新加载"].isEnabled())
        self.assertFalse(buttons["编辑"].isEnabled())
        self.assertFalse(buttons["保存"].isEnabled())
        self.assertFalse(buttons["删除"].isEnabled())
        self.assertFalse(buttons["保存触发设置"].isEnabled())
        button_texts = {button.text() for button in self.window.findChildren(QPushButton)}
        self.assertNotIn("启用", button_texts)
        self.assertNotIn("校验", button_texts)
        macro_table = self.window.findChild(QTableWidget, "macro_library_table")
        self.assertEqual(
            [macro_table.horizontalHeaderItem(index).text() for index in range(macro_table.columnCount())],
            ["序号", "Python 宏"],
        )
        self.assertIsInstance(macro_table.parentWidget().layout(), QHBoxLayout)
        action_panel = self.window.findChild(QWidget, "macro_action_panel")
        self.assertIsInstance(action_panel.layout(), QVBoxLayout)
        self.assertTrue(
            all(
                field.isReadOnly()
                for field in self.window.findChildren(QLineEdit)
                if field.objectName() != "macro_name_field"
                and not field.objectName().startswith("game_keybind_")
            )
        )

    @unittest.skip("Stage 6B 触发详情不再只读")
    def test_trigger_page_uses_chinese_read_only_labels(self):
        label_values = {
            label.text() for label in self.window.findChildren(QLabel)
        }
        field_values = {
            field.text() for field in self.window.findChildren(QLineEdit)
        }
        self.assertTrue({"模式", "次数", "速度", "状态"}.issubset(label_values))
        self.assertIn("未选择有效宏", field_values)
        self.assertIn("F9", field_values)
        trigger_table = self.window.findChild(QTableWidget, "trigger_table")
        self.assertEqual(
            [trigger_table.horizontalHeaderItem(index).text() for index in range(trigger_table.columnCount())],
            ["序号", "名称", "按键", "模式", "状态"],
        )
        self.assertEqual(trigger_table.horizontalHeader().defaultAlignment(), Qt.AlignmentFlag.AlignCenter)
        self.assertEqual(
            trigger_table.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.window.findChild(QTabWidget, "main_tabs").setCurrentIndex(1)
        self.window.show()
        self.app.processEvents()
        self.assertEqual(trigger_table.horizontalScrollBar().maximum(), 0)
        self.assertEqual(trigger_table.horizontalScrollBar().value(), 0)

    def test_features_are_disabled_and_f2_is_only_a_label(self):
        feature_button = next(
            button
            for button in self.window.findChildren(QPushButton)
            if button.text() == "应用功能设置"
        )
        self.assertFalse(feature_button.isEnabled())
        combo_values = {
            combo.currentText() for combo in self.window.findChildren(QComboBox)
        }
        field_values = {field.text() for field in self.window.findChildren(QLineEdit)}
        self.assertIn("F2（仅占位）", combo_values)
        self.assertIn("仅 UI 占位，不注册", field_values)

    def test_settings_page_exposes_editable_game_keybinds_and_save_button(self):
        panel = self.window.findChild(GameKeybindsPanel)
        self.assertIsNotNone(panel)
        self.assertEqual(
            panel.findChild(QLineEdit, "game_keybind_character_1").text(), "1"
        )
        self.assertTrue(panel.findChild(QPushButton, "save_game_keybinds_button").isEnabled())

    def test_settings_page_scrolls_without_compressing_game_keybind_rows(self):
        scroll = self.window.findChild(QScrollArea, "settings_scroll_area")
        panel = self.window.findChild(GameKeybindsPanel)
        self.assertIsNotNone(scroll)
        self.assertEqual(scroll.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.assertGreaterEqual(panel.minimumHeight(), panel.sizeHint().height())
        fields = [
            panel.findChild(QLineEdit, f"game_keybind_{name}")
            for name in ("character_1", "character_2", "character_3", "skill", "echo", "ultimate", "jump", "execute")
        ]
        self.window.findChild(QTabWidget, "main_tabs").setCurrentIndex(3)
        self.window.show()
        self.app.processEvents()
        for field in fields:
            scroll.ensureWidgetVisible(field)
            self.assertGreaterEqual(field.height(), 22)
        self.assertGreater(
            panel.findChild(QPushButton, "save_game_keybinds_button").pos().y(),
            fields[-1].pos().y(),
        )

    def test_mature_rose_theme_is_applied(self):
        stylesheet = self.window.styleSheet()
        for color in ("#FCF7FA", "#C984A1", "#6E4055", "#D8D0D6"):
            self.assertIn(color, stylesheet)

    @unittest.skip("Stage 6B 每个已启用宏均注册自己的触发键")
    def test_complete_window_registers_only_f9_and_f12(self):
        runtime = Mock()
        runtime.current.return_value = SimpleNamespace(mode="switch", count=1)
        manager = Mock()

        with patch("main.HotkeyManager", return_value=manager), patch("main.OsdPopup"):
            window = MainWindow(runtime)

        self.assertEqual([call.args[0] for call in manager.register.call_args_list], ["f9"])
        manager.set_global_disable_key.assert_called_once_with("f12")
        manager.start.assert_called_once()
        window.deleteLater()

    @unittest.skip("Stage 6B 状态改为每个宏独立启用，不再唯一活动宏")
    def test_activity_status_is_unique_and_invalidated_macro_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.py"
            second = root / "second.py"
            invalid = root / "invalid.py"
            first.write_text(VALID_MACRO.replace('NAME="x"', 'NAME="first"'), encoding="utf-8")
            second.write_text(VALID_MACRO.replace('NAME="x"', 'NAME="second"'), encoding="utf-8")
            invalid.write_text("NAME = 'invalid'\n", encoding="utf-8")
            runtime = PythonMacroRuntime()
            manager = Mock()

            with patch("main._MACRO_ROOT", root):
                with patch("main.HotkeyManager", return_value=manager), patch("main.OsdPopup"):
                    window = MainWindow(runtime)

                panel = window._macro_panel
                rows = {entry.path.name: index for index, entry in enumerate(panel.entries)}
                first_row = rows["first.py"]
                second_row = rows["second.py"]
                invalid_row = rows["invalid.py"]
                self.assertEqual(
                    [panel.table.item(first_row, column).text() for column in range(2)],
                    [str(first_row + 1), "first"],
                )
                self.assertEqual(panel.table.item(invalid_row, 1).text(), "invalid")
                self.assertEqual(panel.table.item(invalid_row, 1).foreground().color().name(), "#ff0000")
                panel.table.selectRow(first_row)
                self.assertIsNone(runtime.selected_path())
                self.assertEqual(panel._name_field.text(), "first")
                self.assertTrue(panel._edit_button.isEnabled())
                self.assertTrue(panel._save_button.isEnabled())
                trigger_rows = {
                    window._trigger_table.item(row, 1).text(): row
                    for row in range(window._trigger_table.rowCount())
                }
                self.assertEqual(set(trigger_rows), {"first", "second", "invalid"})
                self.assertEqual(
                    [window._trigger_table.item(row, 0).text() for row in range(window._trigger_table.rowCount())],
                    ["1", "2", "3"],
                )
                self.assertEqual(window._trigger_table.item(trigger_rows["first"], 2).text(), "F9")
                self.assertEqual(window._trigger_table.item(trigger_rows["first"], 3).text(), "切换")
                self.assertEqual(window._trigger_table.item(trigger_rows["invalid"], 4).text(), "不可启用")
                self.assertEqual(
                    window._trigger_table.item(trigger_rows["invalid"], 1).foreground().color().name(),
                    "#ff0000",
                )
                for row in range(window._trigger_table.rowCount()):
                    for column in range(window._trigger_table.columnCount()):
                        self.assertEqual(
                            window._trigger_table.item(row, column).textAlignment(),
                            int(Qt.AlignmentFlag.AlignCenter),
                        )
                window._trigger_table.selectRow(trigger_rows["first"])
                self.assertEqual(window._trigger_mode_field.text(), "切换")
                self.assertEqual(window._trigger_count_field.text(), "1")
                self.assertEqual(window._trigger_speed_field.text(), "1.0")
                self.assertEqual(window._trigger_status_field.text(), "禁用")

                window._on_trigger_cell_clicked(trigger_rows["first"], 4)
                self.assertEqual(runtime.selected_path(), first)
                self.assertEqual(window._trigger_table.item(trigger_rows["first"], 4).text(), "启用")
                self.assertTrue(panel._edit_button.isEnabled())
                self.assertTrue(panel._save_button.isEnabled())
                self.assertTrue(panel._delete_button.isEnabled())
                window._on_trigger_cell_clicked(trigger_rows["second"], 4)
                self.assertEqual(runtime.selected_path(), second)
                self.assertEqual(window._trigger_table.item(trigger_rows["first"], 4).text(), "禁用")
                self.assertEqual(window._trigger_table.item(trigger_rows["second"], 4).text(), "启用")
                window._on_trigger_cell_clicked(trigger_rows["second"], 4)
                self.assertIsNone(runtime.selected_path())
                window._on_trigger_cell_clicked(trigger_rows["invalid"], 4)
                self.assertIsNone(runtime.selected_path())

                window._on_trigger_cell_clicked(trigger_rows["first"], 4)
                window._dispatcher.stop_active_execution = Mock()
                first.write_text("NAME = 'broken'\n", encoding="utf-8")
                panel.refresh()
                self.assertIsNone(runtime.selected_path())
                window._dispatcher.stop_active_execution.assert_called_once()
                manager.mark_finished.assert_called_once_with("f9")
                self.assertEqual(panel.table.item(first_row, 1).text(), "first")
                self.assertEqual(panel.table.item(first_row, 1).foreground().color().name(), "#ff0000")

                panel._schedule_refresh(str(second))
                self.assertTrue(panel.refresh_timer.isActive())
                window.close()

    @unittest.skip("Stage 6B 删除通过每宏绑定停止，不再依赖 F9 当前选择")
    def test_active_macro_rename_preserves_activity_for_next_f9_and_delete_stops_first(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "first.py"
            original.write_text(VALID_MACRO.replace('NAME="x"', 'NAME="first"'), encoding="utf-8")
            runtime = PythonMacroRuntime()
            manager = Mock()
            with patch("main._MACRO_ROOT", root), patch("main.HotkeyManager", return_value=manager), patch("main.OsdPopup"):
                window = MainWindow(runtime)
            panel = window._macro_panel
            window._on_trigger_cell_clicked(0, 4)
            panel.table.selectRow(0)
            panel._name_field.setText("renamed")
            panel._rename_selected_macro()
            renamed = root / "renamed.py"
            self.assertEqual(runtime.selected_path(), renamed)
            self.assertFalse(original.exists())
            self.assertTrue(renamed.exists())
            self.assertEqual(window._active_macro_path, renamed)

            window._dispatcher.stop_active_execution = Mock()
            with patch("src.core.macro_file_manager._move_to_windows_recycle_bin", side_effect=lambda path: path.unlink()), patch.object(
                panel, "_confirm_delete", return_value=True
            ):
                panel._delete_button.click()
            self.assertFalse(renamed.exists())
            self.assertIsNone(runtime.selected_path())
            self.assertIsNone(window._active_macro_path)
            window._dispatcher.stop_active_execution.assert_called_once()
            manager.mark_finished.assert_called_once_with("f9")
            window.close()

    def test_delete_confirmation_cancel_keeps_selected_macro(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            macro = root / "first.py"
            macro.write_text(VALID_MACRO, encoding="utf-8")
            panel = MacroLibraryPanel(root)
            panel.table.selectRow(0)
            callback = Mock()
            panel._on_delete_requested = callback
            with patch.object(panel, "_confirm_delete", return_value=False):
                panel._delete_button.click()
            callback.assert_not_called()
            self.assertTrue(macro.exists())
            panel.deleteLater()

    def test_name_enter_uses_the_same_safe_rename_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "first.py"
            original.write_text(
                VALID_MACRO.replace('NAME="x"', 'NAME="first"'), encoding="utf-8"
            )
            panel = MacroLibraryPanel(root)
            panel.table.selectRow(0)
            panel._name_field.setText("renamed")

            QTest.keyClick(panel._name_field, Qt.Key.Key_Return)
            self.app.processEvents()

            renamed = root / "renamed.py"
            self.assertTrue(renamed.is_file())
            self.assertFalse(original.exists())
            self.assertIn("NAME='renamed'", renamed.read_text(encoding="utf-8"))
            self.assertEqual(panel.table.item(0, 1).text(), "renamed")
            panel.deleteLater()

    def test_python_editor_uses_chinese_buttons_highlighting_and_python_indentation(self):
        source = 'def run(player):\n    # 注释\n    value = "彩色"\n'
        parent = QWidget()
        dialog = MacroEditorDialog(parent, "新建 Python 宏", "测试", source, lambda *_: None)
        buttons = {button.text() for button in dialog.findChildren(QPushButton)}
        self.assertTrue({"保存", "取消"}.issubset(buttons))
        editor = dialog.source_editor
        editor.setPlainText("pass")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        editor.setFocus()
        QTest.keyClick(editor, Qt.Key.Key_Tab)
        self.assertEqual(editor.toPlainText(), "pass    ")

        editor.setPlainText("def run(player):")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        QTest.keyClick(editor, Qt.Key.Key_Return)
        self.assertEqual(editor.toPlainText(), "def run(player):\n    ")

        editor.setPlainText("    player.sleep(50)")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        QTest.keyClick(editor, Qt.Key.Key_Return)
        self.assertEqual(editor.toPlainText(), "    player.sleep(50)\n    ")

        editor.setPlainText("first\nsecond")
        cursor = editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor.setTextCursor(cursor)
        QTest.keyClick(editor, Qt.Key.Key_Tab)
        self.assertEqual(editor.toPlainText(), "    first\n    second")

        editor.setPlainText(source)
        editor.highlighter.rehighlight()
        self.app.processEvents()
        formats = editor.document().firstBlock().layout().formats()
        self.assertTrue(formats)
        self.assertTrue(any(item.format.foreground().color().isValid() for item in formats))
        dialog.deleteLater()
        parent.deleteLater()

    def test_ai_prompt_is_always_available_read_only_and_copies_the_current_api_template(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt_config = root / "prompt_config"
            prompt_config.mkdir()
            shipped_default = Path(__file__).resolve().parents[1] / "config" / "ai_prompt.default.txt"
            (prompt_config / "ai_prompt.default.txt").write_text(
                shipped_default.read_text(encoding="utf-8"), encoding="utf-8"
            )
            macro = root / "first.py"
            source = VALID_MACRO.replace('NAME="x"', 'NAME="first"') + "# 保留的源码注释\n"
            macro.write_text(source, encoding="utf-8")
            panel = MacroLibraryPanel(root, prompt_config_dir=prompt_config)
            actions = panel.findChild(QWidget, "macro_action_panel").layout()
            self.assertLess(actions.indexOf(panel._edit_button), actions.indexOf(panel._ai_prompt_button))
            self.assertTrue(panel._ai_prompt_button.isEnabled())

            general_prompt = panel._build_ai_prompt()
            self.assertEqual(
                (prompt_config / "ai_prompt.txt").read_text(encoding="utf-8"),
                (prompt_config / "ai_prompt.default.txt").read_text(encoding="utf-8"),
            )
            self.assertIn("二、当前能够直接使用的函数", general_prompt)
            self.assertIn("player.tap(key, hold_ms=20)", general_prompt)
            self.assertIn("player.sleep(ms)", general_prompt)
            for method in ("切换(1|2|3)", "战技()", "声骸()", "大招()", "跳跃()", "处决()"):
                self.assertIn(f"player.{method}", general_prompt)
            self.assertIn("HOTKEY：必须固定写为 \"f9\"", general_prompt)
            self.assertIn("Q：声骸技能", general_prompt)
            self.assertIn("R：大招", general_prompt)
            self.assertIn("1号角色名称：", general_prompt)
            self.assertIn("2号角色名称：", general_prompt)
            self.assertIn("3号角色名称：", general_prompt)
            for direction in ("1→2", "1→3", "2→1", "2→3", "3→1", "3→2"):
                self.assertIn(direction, general_prompt)
            self.assertIn("至少 50ms", general_prompt)
            self.assertIn("至少 1080ms", general_prompt)
            self.assertIn("1000ms 冷却和额外 80ms 安全余量", general_prompt)
            self.assertIn('player.sleep(50)\nplayer.tap("2")', general_prompt)
            self.assertIn('player.tap("2")\nplayer.sleep(1080)\nplayer.tap("1")', general_prompt)
            self.assertIn('player.tap("R")\nplayer.sleep(1500)\nplayer.tap("1")', general_prompt)
            r_example = general_prompt.split("大招后直接切人示例：", 1)[1].split(
                "三角色顺序切换示例：", 1
            )[0]
            self.assertNotIn("player.sleep(50)", r_example)
            self.assertNotIn("player.sleep(1080)", r_example)
            self.assertIn("角色编号说明注释", general_prompt)
            self.assertIn("player.切换(1)、player.切换(2)、player.切换(3)", general_prompt)
            self.assertNotIn("小技能", general_prompt)
            self.assertNotIn("##", general_prompt)
            self.assertNotIn("```", general_prompt)
            self.assertNotIn("\n- ", general_prompt)
            self.assertNotIn("#", general_prompt)
            self.assertNotIn("BaseChar.py", general_prompt)

            panel.table.selectRow(0)
            selected_prompt = panel._build_ai_prompt()
            self.assertIn(source, selected_prompt)
            self.assertIn("# 保留的源码注释", selected_prompt)
            self.assertNotIn("```python", selected_prompt)
            dialog = AiPromptDialog(panel, selected_prompt)
            self.assertTrue(dialog.prompt_editor.isReadOnly())
            self.assertEqual(dialog.copy_button.text(), "复制提示词")
            dialog.copy_button.click()
            self.assertEqual(QApplication.clipboard().text(), selected_prompt)
            self.assertEqual(dialog.copy_status.text(), "提示词已复制，请粘贴给 AI")
            dialog.deleteLater()

            macro.write_text("NAME = 'invalid'\n", encoding="utf-8")
            panel.refresh()
            panel.table.selectRow(0)
            self.assertTrue(panel._ai_prompt_button.isEnabled())
            self.assertNotIn(source, panel._build_ai_prompt())
            with patch.object(panel._manager, "read_source", side_effect=MacroFileError("read failed")):
                self.assertNotIn(source, panel._build_ai_prompt())
            panel.deleteLater()

    def test_ai_prompt_files_are_editable_reloaded_and_fail_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            config_dir = Path(directory) / "config"
            config_dir.mkdir()
            default_path = config_dir / "ai_prompt.default.txt"
            current_path = config_dir / "ai_prompt.txt"
            default_text = "默认模板\nplayer.tap(\"R\")\nplayer.sleep(1800)"
            default_path.write_text(default_text, encoding="utf-8")

            first = build_ai_prompt_content(config_dir=config_dir)
            self.assertEqual(current_path.read_text(encoding="utf-8"), default_text)
            self.assertIn("已从默认备份恢复", first.load.notice)
            self.assertEqual(first.load.current_path, current_path.resolve())
            self.assertEqual(first.load.default_path, default_path.resolve())

            current_path.write_text("外部修改后的提示词", encoding="utf-8")
            reopened = build_ai_prompt_content(config_dir=config_dir)
            self.assertIn("外部修改后的提示词", reopened.text)
            dialog = AiPromptDialog(self.window, reopened.text, reopened.load)
            self.assertIn(str(current_path.resolve()), dialog.path_info.text())
            self.assertIn(str(default_path.resolve()), dialog.path_info.text())
            dialog.copy_button.click()
            self.assertEqual(QApplication.clipboard().text(), reopened.text)
            dialog.deleteLater()

            original_default = default_path.read_bytes()
            current_path.unlink()
            restored = load_prompt_template(config_dir)
            self.assertEqual(current_path.read_text(encoding="utf-8"), default_text)
            self.assertEqual(default_path.read_bytes(), original_default)
            self.assertIn("已从默认备份恢复", restored.notice)

            invalid_current = b"\xff\xfe\x00"
            current_path.write_bytes(invalid_current)
            fallback = load_prompt_template(config_dir)
            self.assertEqual(fallback.template, default_text)
            self.assertIn("未覆盖当前文件", fallback.notice)
            self.assertEqual(current_path.read_bytes(), invalid_current)
            self.assertEqual(default_path.read_bytes(), original_default)

            default_path.write_bytes(b"\xff")
            unavailable = build_ai_prompt_content(config_dir=config_dir)
            self.assertIn("无法读取", unavailable.text)
            self.assertIn("没有写入任何文件", unavailable.load.notice)
            self.assertEqual(current_path.read_bytes(), invalid_current)

    @unittest.skip("Stage 6B 重载会按所有已启用宏重新注册触发键")
    def test_manual_reload_adds_external_macro_without_changing_active_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.py"
            first.write_text(
                VALID_MACRO.replace('NAME="x"', 'NAME="first"'), encoding="utf-8"
            )
            runtime = PythonMacroRuntime()
            manager = Mock()

            with patch("main._MACRO_ROOT", root):
                with patch("main.HotkeyManager", return_value=manager), patch("main.OsdPopup"):
                    window = MainWindow(runtime)

                panel = window._macro_panel
                first_row = next(
                    row for row, entry in enumerate(panel.entries) if entry.path == first
                )
                window._on_trigger_cell_clicked(first_row, 4)
                self.assertEqual(runtime.selected_path(), first)
                register_count = manager.register.call_count

                external = root / "external.py"
                external.write_text(
                    VALID_MACRO.replace('NAME="x"', 'NAME="external"'), encoding="utf-8"
                )
                panel._reload_button.click()

                self.assertEqual(runtime.selected_path(), first)
                self.assertEqual(manager.register.call_count, register_count)
                self.assertEqual(
                    {entry.path.name for entry in panel.entries}, {"first.py", "external.py"}
                )
                self.assertEqual(
                    {
                        window._trigger_table.item(row, 1).text()
                        for row in range(window._trigger_table.rowCount())
                    },
                    {"first", "external"},
                )
                self.assertEqual(
                    window._trigger_table.item(
                        next(
                            row
                            for row in range(window._trigger_table.rowCount())
                            if window._trigger_table.item(row, 1).text() == "first"
                        ),
                        4,
                    ).text(),
                    "启用",
                )
                window.close()

    def test_close_stops_and_cleans_up_dependencies(self):
        window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(window)
        window._dispatcher = Mock()
        window._hotkey_mgr = Mock()
        window._osd_popup = Mock()

        with patch("main.keyboard.unhook_all") as unhook_all:
            window.close()

        window._dispatcher.stop_active_execution.assert_called_once()
        unhook_all.assert_called_once()
        window._hotkey_mgr.stop.assert_called_once()
        window._osd_popup.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
