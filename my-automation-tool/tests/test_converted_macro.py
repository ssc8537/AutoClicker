import ast
import unittest
from pathlib import Path

from src.core.macro_library import validate_macro_source


class ConvertedMacroTests(unittest.TestCase):
    def test_yangyang_linna_qianxiao_macro_preserves_json_contract(self):
        path = Path(__file__).resolve().parents[1] / "macros" / "(二)秧秧琳奈千咲.py"
        source = path.read_text(encoding="utf-8")
        metadata = validate_macro_source(source, filename=str(path))

        self.assertEqual(metadata.hotkey, "mouse_back")
        self.assertEqual(metadata.mode, "down")
        self.assertEqual(metadata.count, 0)
        self.assertIsInstance(metadata.enabled, bool)
        for name in ("秧秧", "琳奈", "千咲"):
            self.assertIn(name, source)
        for wrong_name in ("卡提", "夏空", "千笑"):
            self.assertNotIn(wrong_name, source)

        tree = ast.parse(source)
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
        self.assertEqual(sorted(loop_counts), [5, 8, 8, 100])


if __name__ == "__main__":
    unittest.main()
