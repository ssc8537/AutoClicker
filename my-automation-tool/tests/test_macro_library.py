import tempfile
import unittest
from pathlib import Path

from src.core.macro_library import scan_macro_root


VALID = 'NAME="x"\nHOTKEY="f9"\nMODE="switch"\nCOUNT=1\nSPEED=1\ndef run(player): pass\n'


class MacroLibraryTests(unittest.TestCase):
    def test_scans_top_level_and_reports_invalid_entries_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "valid.py").write_text(VALID, encoding="utf-8")
            (root / "bad.py").write_text("def run(:\n", encoding="utf-8")
            (root / "side_effect.py").write_text(
                'NAME="safe"\nHOTKEY="f9"\nMODE="switch"\nCOUNT=1\nSPEED=1\n'
                'raise RuntimeError("扫描时不得执行")\ndef run(player): pass\n',
                encoding="utf-8",
            )
            (root / "__init__.py").write_text("", encoding="utf-8")
            (root / ".hidden.py").write_text(VALID, encoding="utf-8")
            (root / "~temporary.py").write_text(VALID, encoding="utf-8")
            (root / "child").mkdir()
            entries = scan_macro_root(root)
            self.assertEqual(
                [entry.path.name for entry in entries],
                ["bad.py", "side_effect.py", "valid.py"],
            )
            self.assertFalse(entries[0].valid)
            self.assertTrue(entries[1].valid)
            self.assertTrue(entries[2].valid)
            self.assertEqual(entries[1].macro.name, "safe")

    def test_rejects_missing_run_and_dynamic_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "missing_run.py").write_text(
                'NAME="x"\nHOTKEY="f9"\nMODE="switch"\nCOUNT=1\nSPEED=1\n',
                encoding="utf-8",
            )
            (root / "dynamic.py").write_text(
                'NAME="x"\nHOTKEY="f9"\nMODE="switch"\nCOUNT=1 + 1\nSPEED=1\ndef run(player): pass\n',
                encoding="utf-8",
            )
            entries = scan_macro_root(root)
            self.assertTrue(all(not entry.valid for entry in entries))
            self.assertIn("必须定义 run", entries[1].error)
            self.assertIn("必须是字面量", entries[0].error)

    def test_rejects_only_f12_and_allows_duplicate_hotkeys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "reserved.py").write_text(VALID.replace('"f9"', '"f12"'), encoding="utf-8")
            (root / "first.py").write_text(VALID.replace('"f9"', '"f1"'), encoding="utf-8")
            (root / "second.py").write_text(VALID.replace('"f9"', '"f1"'), encoding="utf-8")
            entries = {entry.path.name: entry for entry in scan_macro_root(root)}
            self.assertFalse(entries["reserved.py"].valid)
            self.assertIn("F12", entries["reserved.py"].error)
            self.assertTrue(entries["first.py"].valid)
            self.assertTrue(entries["second.py"].valid)
