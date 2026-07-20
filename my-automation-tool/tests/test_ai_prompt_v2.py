import json
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
    display_input_key,
)
from src.core.macro_library import validate_macro_source
from src.ui.ai_prompt_dialog import build_ai_prompt_content


class AiPromptV2Tests(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[1]
        self.default_prompt = self.project_root / "config" / "ai_prompt.default.txt"

    def _prompt_root(self, directory: str) -> Path:
        root = Path(directory)
        template = self.default_prompt.read_text(encoding="utf-8")
        (root / "ai_prompt.default.txt").write_text(template, encoding="utf-8")
        (root / "ai_prompt.txt").write_text(template, encoding="utf-8")
        return root

    def test_prompt_uses_live_global_key_and_shared_action_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._prompt_root(directory)
            labels = {**DEFAULT_KEYBIND_LABELS, "ultimate": "终结技", "extension_1": "闪避反击"}
            values = {**DEFAULT_KEYBIND_VALUES, "ultimate": "mouse_forward", "extension_1": "f16"}
            save_game_keybinds(GameKeybinds(values, labels), root / "game_keybinds.ini")
            save_global_hotkey("f24", root / "global_hotkey.ini")

            prompt = build_ai_prompt_content(config_dir=root).text

            self.assertIn('当前全局启停键：内部值 "f24"；界面显示 "F24"', prompt)
            self.assertIn('当前名称 "终结技"；物理键内部值 "mouse_forward"', prompt)
            self.assertIn('player.大招()；也可写 player.按键("终结技")', prompt)
            self.assertIn('当前名称 "闪避反击"；物理键内部值 "f16"', prompt)
            self.assertIn('调用 player.按键("闪避反击")', prompt)

    def test_prompt_dictionary_tracks_every_supported_key(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt = build_ai_prompt_content(config_dir=self._prompt_root(directory)).text

            for key, vk in WINDOWS_VK_BY_KEY.items():
                expected = (
                    f"{json.dumps(key, ensure_ascii=False)} -> "
                    f"{json.dumps(display_input_key(key), ensure_ascii=False)} -> 0x{vk:02X}"
                )
                self.assertIn(expected, prompt)
            for hotkey, button in MOUSE_BUTTON_FOR_HOTKEY.items():
                expected = (
                    f"{json.dumps(hotkey, ensure_ascii=False)} -> "
                    f"{json.dumps(display_input_key(hotkey), ensure_ascii=False)} -> "
                    f"{json.dumps(button, ensure_ascii=False)}"
                )
                self.assertIn(expected, prompt)

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
                self.assertIn(f"{metadata}：", prompt)
            for field in (
                "普通攻击", "战技", "声骸", "大招或共鸣解放", "入场效果",
                "退场效果", "特殊资源", "增益窗口", "可取消时刻",
            ):
                self.assertIn(field, prompt)
            self.assertIn("不得编造具体角色技能", prompt)
            self.assertIn("不支持：键盘长按 API", prompt)
            self.assertIn("不写进 Python 宏", prompt)

    def test_all_complete_examples_pass_current_static_validator(self):
        template = self.default_prompt.read_text(encoding="utf-8")
        for label in ("A", "B", "C"):
            match = re.search(
                rf"示例 {label}（[^\n]+）开始\n(?P<source>.*?)\n示例 {label} 结束",
                template,
                flags=re.DOTALL,
            )
            self.assertIsNotNone(match, f"找不到示例 {label}")
            validate_macro_source(match.group("source"), filename=f"示例 {label}")

    def test_shipped_current_and_default_templates_match(self):
        current = self.project_root / "config" / "ai_prompt.txt"
        self.assertEqual(current.read_bytes(), self.default_prompt.read_bytes())


if __name__ == "__main__":
    unittest.main()
