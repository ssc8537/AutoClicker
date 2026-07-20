import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.game_keybinds import (
    DEFAULT_GAME_KEYBINDS,
    KEYBIND_NAMES,
    GameKeybindError,
    GameKeybinds,
    load_game_keybinds,
    save_game_keybinds,
)


class GameKeybindTests(unittest.TestCase):
    def test_missing_file_uses_defaults_and_round_trips_after_atomic_save(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game_keybinds.ini"
            self.assertEqual(load_game_keybinds(path), DEFAULT_GAME_KEYBINDS)
            custom = GameKeybinds({
                "character_1": "4", "character_2": "5", "character_3": "6",
                "skill": "a", "echo": "b", "ultimate": "c", "jump": "space", "execute": "d",
            })
            save_game_keybinds(custom, path)
            self.assertIn("jump = space", path.read_text(encoding="utf-8"))
            self.assertEqual(load_game_keybinds(path), custom)

    def test_rejects_unsupported_but_allows_duplicate_keys_and_f2_f9_f12(self):
        values = dict(DEFAULT_GAME_KEYBINDS.values)
        for name, value in (("skill", "mouse1"),):
            invalid = dict(values)
            invalid[name] = value
            with self.assertRaises(GameKeybindError):
                GameKeybinds(invalid)
        duplicate = dict(values)
        duplicate["skill"] = "1"
        self.assertEqual(GameKeybinds(duplicate).key_for("skill"), "1")
        allowed = dict(values)
        allowed["skill"] = "f12"
        self.assertEqual(GameKeybinds(allowed).key_for("skill"), "f12")

    def test_accepts_all_five_mouse_buttons(self):
        for index, mouse_key in enumerate((
            "mouse_left", "mouse_right", "mouse_middle", "mouse_back", "mouse_forward",
        )):
            values = dict(DEFAULT_GAME_KEYBINDS.values)
            values[KEYBIND_NAMES[index]] = mouse_key
            self.assertEqual(GameKeybinds(values).key_for(KEYBIND_NAMES[index]), mouse_key)

    def test_custom_extension_labels_round_trip_and_can_share_the_same_key(self):
        values = dict(DEFAULT_GAME_KEYBINDS.values)
        values["extension_1"] = "r"
        values["extension_2"] = "r"
        labels = {
            **{name: name for name in KEYBIND_NAMES},
            "extension_1": "大招 1", "extension_2": "大招 2",
        }
        keybinds = GameKeybinds(values, labels)
        self.assertEqual(keybinds.key_for_label("大招 1"), "r")
        self.assertEqual(keybinds.key_for_label("大招 2"), "r")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game_keybinds.ini"
            save_game_keybinds(keybinds, path)
            self.assertEqual(load_game_keybinds(path), keybinds)

    def test_core_action_names_are_editable(self):
        labels = {name: name for name in KEYBIND_NAMES}
        labels["ultimate"] = "不应保存"
        keybinds = GameKeybinds(dict(DEFAULT_GAME_KEYBINDS.values), labels)
        self.assertEqual(keybinds.label_for("ultimate"), "不应保存")

    def test_invalid_saved_file_is_rejected_without_fallback_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game_keybinds.ini"
            original = "[game_keybinds]\nskill = F9\n"
            path.write_text(original, encoding="utf-8")
            with self.assertRaises(GameKeybindError):
                load_game_keybinds(path)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_replace_failure_preserves_old_valid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "game_keybinds.ini"
            save_game_keybinds(DEFAULT_GAME_KEYBINDS, path)
            original = path.read_text(encoding="utf-8")
            with patch("src.core.game_keybinds.os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(GameKeybindError):
                    save_game_keybinds(DEFAULT_GAME_KEYBINDS, path)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
