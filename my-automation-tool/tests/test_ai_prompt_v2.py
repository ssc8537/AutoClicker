import re
import tempfile
import unittest
from pathlib import Path

from src.core.game_keybinds import (
    DEFAULT_KEYBIND_LABELS,
    DEFAULT_KEYBIND_VALUES,
    GameKeybinds,
    save_game_keybinds,
)
from src.core.global_hotkey import save_global_hotkey
from src.core.input_keys import (
    MOUSE_BUTTON_FOR_HOTKEY,
    WINDOWS_VK_BY_KEY,
)
from src.core.macro_library import validate_macro_source
from src.ui.ai_prompt_dialog import build_ai_prompt_content, load_prompt_template


class AiPromptV2Tests(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[1]
        self.default_prompt = self.project_root / "config" / "ai_prompt.default.md"

    def _prompt_root(self, directory: str) -> Path:
        root = Path(directory)
        template = self.default_prompt.read_text(encoding="utf-8")
        (root / "ai_prompt.default.md").write_text(template, encoding="utf-8")
        (root / "ai_prompt.md").write_text(template, encoding="utf-8")
        return root

    def test_prompt_uses_live_global_key_and_shared_action_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._prompt_root(directory)
            labels = {**DEFAULT_KEYBIND_LABELS, "ultimate": "终结技", "extension_1": "闪避反击"}
            values = {**DEFAULT_KEYBIND_VALUES, "ultimate": "mouse_forward", "extension_1": "f16"}
            save_game_keybinds(GameKeybinds(values, labels), root / "game_keybinds.ini")
            save_global_hotkey("f24", root / "global_hotkey.ini")

            prompt = build_ai_prompt_content(config_dir=root).text

            self.assertIn('**当前全局启停键：** 内部值 `f24`，界面显示 **F24**', prompt)
            self.assertIn('| `ultimate` | 终结技 | `mouse_forward` |', prompt)
            self.assertIn('`player.大招()` / `player.按键("终结技")`', prompt)
            self.assertIn('| `extension_1` | 闪避反击 | `f16` |', prompt)
            self.assertIn('`player.按键("闪避反击")`', prompt)

    def test_prompt_dictionary_tracks_every_supported_key(self):
        template = self.default_prompt.read_text(encoding="utf-8")
        self.assertIn("## 9. 完整按键字典（键盘与鼠标）", template)
        for key in WINDOWS_VK_BY_KEY:
            self.assertRegex(template, rf"\| `{re.escape(key)}` \|")
        for hotkey, button in MOUSE_BUTTON_FOR_HOTKEY.items():
            self.assertRegex(template, rf"\| `{re.escape(hotkey)}` \|")
            self.assertIn(f"| `{button}` |", template)

        with tempfile.TemporaryDirectory() as directory:
            content = build_ai_prompt_content(config_dir=self._prompt_root(directory))
            prompt = content.text
            self.assertEqual(prompt.count("## 9. 完整按键字典（键盘与鼠标）"), 1)
            self.assertEqual(prompt.count("## 10. 当前程序设置"), 1)
            self.assertEqual(prompt.count("## 11. 已保存的宏源码"), 1)
            self.assertIsNotNone(content.complete_path)
            self.assertEqual(
                content.complete_path.read_text(encoding="utf-8"), prompt
            )

    def test_prompt_documents_complete_real_api_and_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt = build_ai_prompt_content(config_dir=self._prompt_root(directory)).text

            for call in (
                "player.tap(", "player.sleep(", "player.切换(", "player.战技(",
                "player.声骸(", "player.大招(", "player.跳跃(", "player.处决(",
                "player.按键(", "player.mouse_click(", "player.mouse_down(",
                "player.mouse_up(", "player.mouse_repeat(",
            ):
                self.assertIn(call, prompt)
            for metadata in ("NAME", "HOTKEY", "MODE", "COUNT", "SPEED", "ENABLED"):
                self.assertIn(f"| `{metadata}` |", prompt)
            for field in (
                "普通攻击", "战技", "声骸", "大招或共鸣解放", "入场效果",
                "退场效果", "特殊资源", "增益窗口", "可取消时刻",
            ):
                self.assertIn(field, prompt)
            self.assertIn("不得编造具体角色技能", prompt)
            self.assertIn("不支持：键盘长按 API", prompt)
            self.assertIn("不写进 Python 宏", prompt)
            for artifact in (
                "events.jsonl",
                "events.csv",
                "raw.mp4",
                "raw.ass",
                "input_subtitles.srt",
                "metadata.json",
                "native.log",
            ):
                self.assertIn(f"`{artifact}`", prompt)
            for field in (
                "held_ms",
                "release_gap_ms",
                "delta_from_previous_event_ms",
                "overlap_keys",
                "active_keys_after_event",
            ):
                self.assertIn(f"`{field}`", prompt)
            self.assertIn("Python宏不允许控制录像", prompt)
            self.assertIn("不证明技能成功", prompt)
            self.assertIn("for _ in range(次数)", prompt)
            self.assertIn("不同的毫秒节奏", prompt)

    def test_all_complete_examples_pass_current_static_validator(self):
        template = self.default_prompt.read_text(encoding="utf-8")
        for label in ("A", "B", "C", "D"):
            match = re.search(
                rf"### 示例 {label}：[^\n]+\n\n```python\n(?P<source>.*?)\n```",
                template,
                flags=re.DOTALL,
            )
            self.assertIsNotNone(match, f"找不到示例 {label}")
            source = match.group("source")
            validate_macro_source(source, filename=f"示例 {label}")
            for metadata in ("NAME", "HOTKEY", "MODE", "COUNT", "SPEED", "ENABLED"):
                self.assertRegex(source, rf"(?m)^{metadata}\s*=.*#.+$")
            self.assertRegex(source, r"(?m)^\s+#.+$")

    def test_shipped_current_and_default_templates_match(self):
        current = self.project_root / "config" / "ai_prompt.md"
        self.assertEqual(current.read_bytes(), self.default_prompt.read_bytes())

    def test_legacy_txt_is_migrated_without_deleting_user_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "ai_prompt.txt"
            legacy.write_text("旧版用户提示词", encoding="utf-8")

            loaded = load_prompt_template(root)

            self.assertEqual(loaded.template, "旧版用户提示词")
            self.assertEqual((root / "ai_prompt.md").read_text(encoding="utf-8"), loaded.template)
            self.assertTrue(legacy.exists())
            self.assertIn("迁移为 Markdown", loaded.notice)


if __name__ == "__main__":
    unittest.main()
