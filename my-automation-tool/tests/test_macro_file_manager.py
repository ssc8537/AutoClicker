import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.macro_file_manager import MacroFileError, MacroFileManager
from src.core.macro_library import scan_macro_root


VALID_SOURCE = '''NAME = "first"
HOTKEY = "f9"
MODE = "down"
COUNT = 1
SPEED = 1.0


def run(player):
    pass
'''


class MacroFileManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.manager = MacroFileManager(self.root)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_create_template_is_static_and_scannable(self):
        target = self.manager.create("默认模板")

        self.assertIn('NAME = \'默认模板\'', target.read_text(encoding="utf-8"))
        self.assertTrue(scan_macro_root(self.root)[0].valid)

    def test_create_custom_source_is_static_and_scannable(self):
        marker = self.root / "executed.txt"
        source = VALID_SOURCE + f"\nmarker = Path(r'{marker}').write_text('executed')\n"

        target = self.manager.create("新宏", source)

        self.assertFalse(marker.exists())
        entries = scan_macro_root(self.root)
        self.assertEqual([entry.path for entry in entries], [target])
        self.assertTrue(entries[0].valid)
        self.assertEqual(entries[0].macro.name, "新宏")

    def test_update_renames_file_and_name_metadata(self):
        original = self.manager.create("first", VALID_SOURCE)
        updated_source = VALID_SOURCE.replace("pass", "player.sleep(0)")

        target = self.manager.update(original, "renamed", updated_source)

        self.assertEqual(target.name, "renamed.py")
        self.assertFalse(original.exists())
        self.assertIn("NAME = 'renamed'", target.read_text(encoding="utf-8"))
        self.assertEqual(scan_macro_root(self.root)[0].macro.name, "renamed")

    def test_rejects_illegal_and_conflicting_names_but_allows_active_save_and_rename(self):
        first = self.manager.create("first", VALID_SOURCE)
        self.manager.create("second", VALID_SOURCE)
        original = first.read_text(encoding="utf-8")

        for name in ("bad/name", "CON", "second"):
            with self.assertRaises(MacroFileError):
                self.manager.rename(first, name)
            self.assertEqual(first.read_text(encoding="utf-8"), original)
        renamed = self.manager.rename(first, "renamed", active_path=first)
        self.assertEqual(renamed.name, "renamed.py")
        self.assertFalse(first.exists())
        self.manager.update(renamed, "renamed", VALID_SOURCE.replace("pass", "player.sleep(0)"), active_path=renamed)
        self.assertIn("player.sleep(0)", renamed.read_text(encoding="utf-8"))

    def test_recycle_bin_failure_keeps_file_and_success_uses_controlled_path(self):
        target = self.manager.create("first", VALID_SOURCE)
        with patch("src.core.macro_file_manager._move_to_windows_recycle_bin", side_effect=OSError("blocked")):
            with self.assertRaises(MacroFileError):
                self.manager.move_to_recycle_bin(target)
        self.assertTrue(target.exists())

        def move_to_test_recycle_bin(path):
            path.unlink()

        with patch("src.core.macro_file_manager._move_to_windows_recycle_bin", side_effect=move_to_test_recycle_bin) as recycled:
            self.manager.move_to_recycle_bin(target)
        recycled.assert_called_once_with(target)
        self.assertFalse(target.exists())

    def test_invalid_source_and_write_failure_keep_old_file(self):
        target = self.manager.create("first", VALID_SOURCE)
        original = target.read_text(encoding="utf-8")

        for invalid in (
            VALID_SOURCE.replace("def run(player):", "def run(other):"),
            VALID_SOURCE.replace('COUNT = 1\n', ""),
            "def run(player):\n",
        ):
            with self.assertRaises(MacroFileError):
                self.manager.update(target, "first", invalid)
            self.assertEqual(target.read_text(encoding="utf-8"), original)

        with patch("src.core.macro_file_manager.os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(MacroFileError):
                self.manager.update(target, "first", VALID_SOURCE.replace("pass", "player.sleep(1)"))
        self.assertEqual(target.read_text(encoding="utf-8"), original)

    def test_rename_failure_restores_old_file_without_duplicate_python_files(self):
        original = self.manager.create("first", VALID_SOURCE)
        target = self.root / "renamed.py"
        real_replace = __import__("os").replace

        def fail_target_replace(source, destination):
            if Path(destination) == target:
                raise OSError("target blocked")
            return real_replace(source, destination)

        with patch("src.core.macro_file_manager.os.replace", side_effect=fail_target_replace):
            with self.assertRaises(MacroFileError):
                self.manager.rename(original, "renamed")

        self.assertTrue(original.exists())
        self.assertFalse(target.exists())
        self.assertEqual([path.name for path in self.root.glob("*.py")], ["first.py"])


if __name__ == "__main__":
    unittest.main()
