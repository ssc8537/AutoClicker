import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.game_keybinds import (
    DEFAULT_GAME_KEYBINDS,
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
            self.assertIn("jump = Space", path.read_text(encoding="utf-8"))
            self.assertEqual(load_game_keybinds(path), custom)

    def test_rejects_unsupported_duplicate_and_reserved_keys(self):
        values = dict(DEFAULT_GAME_KEYBINDS.values)
        for name, value in (("skill", "mouse1"), ("skill", "1"), ("skill", "f9")):
            invalid = dict(values)
            invalid[name] = value
            with self.assertRaises(GameKeybindError):
                GameKeybinds(invalid)

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
