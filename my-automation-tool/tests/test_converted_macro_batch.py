import unittest
from pathlib import Path

from src.core.macro_library import validate_macro_source


class CurrentMacroLibraryTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1] / "macros"

    def test_current_top_level_files_are_static_valid_macros(self):
        """用户可持续改名、改键和改循环；这里只校验当前宏，不锁死旧快照。"""
        paths = sorted(self.ROOT.glob("*.py"))
        self.assertTrue(paths)

        for path in paths:
            with self.subTest(filename=path.name):
                source = path.read_text(encoding="utf-8")
                metadata = validate_macro_source(source, filename=str(path))
                self.assertIn(metadata.mode, {"down", "switch"})
                self.assertGreaterEqual(metadata.count, 0)
                self.assertLessEqual(metadata.count, 99)
                self.assertGreater(metadata.speed, 0)
                self.assertIsInstance(metadata.enabled, bool)

    def test_compact_sequences_keep_original_physical_order(self):
        expected = {
            "13EQFR左键.py": ['"1"', '"3"', '"e"', '"q"', '"f"', '"r"', '"mouse_left"'],
        }
        for filename, keys in expected.items():
            with self.subTest(filename=filename):
                source = (self.ROOT / filename).read_text(encoding="utf-8")
                offsets = [source.index(f"_点击(player, {key})") for key in keys]
                self.assertEqual(offsets, sorted(offsets))


if __name__ == "__main__":
    unittest.main()
