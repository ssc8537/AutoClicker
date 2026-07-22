import ast
import unittest
from pathlib import Path

from src.core.macro_library import validate_macro_source


class ConvertedMacroBatchTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1] / "macros"

    EXPECTED = {
        "一_剑切轴.py": ("numpad0", "down", [3, 5, 7, 8, 1000]),
        "一_千咲合轴卡提.py": ("mouse_back", "down", [5, 5, 8, 8, 100]),
        "一_夏空合轴千咲.py": ("mouse_forward", "down", [1, 1, 2, 2, 2, 4, 6, 100]),
        "12eqr左键-今汐.py": ("mouse_back", "down", []),
        "13EQFR左键.py": ("mouse_forward", "down", []),
        "123全切加大招_今汐.py": ("mouse_back", "down", []),
        "1234eqfR左键.py": ("mouse_back", "down", []),
        "1234eqf左键.py": ("mouse_back", "down", []),
    }

    def test_all_converted_files_are_static_valid_macros(self):
        for filename, (hotkey, mode, _) in self.EXPECTED.items():
            with self.subTest(filename=filename):
                path = self.ROOT / filename
                source = path.read_text(encoding="utf-8")
                metadata = validate_macro_source(source, filename=str(path))
                self.assertEqual(metadata.hotkey, hotkey)
                self.assertEqual(metadata.mode, mode)
                self.assertEqual(metadata.count, 0)
                self.assertEqual(metadata.speed, 1.0)
                self.assertIsInstance(metadata.enabled, bool)

    def test_fixed_loop_counts_match_source_json(self):
        for filename, (_, _, expected_loops) in self.EXPECTED.items():
            with self.subTest(filename=filename):
                tree = ast.parse((self.ROOT / filename).read_text(encoding="utf-8"))
                loop_counts = [
                    node.iter.args[0].value
                    for node in ast.walk(tree)
                    if isinstance(node, ast.For)
                    and isinstance(node.iter, ast.Call)
                    and isinstance(node.iter.func, ast.Name)
                    and node.iter.func.id == "range"
                    and len(node.iter.args) == 1
                    and isinstance(node.iter.args[0], ast.Constant)
                ]
                self.assertEqual(sorted(loop_counts), sorted(expected_loops))

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
