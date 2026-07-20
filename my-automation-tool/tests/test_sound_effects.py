import os
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from src.ui.sound_effects import SoundEffects


class SoundEffectsTests(unittest.TestCase):
    def test_automated_gui_tests_can_force_real_audio_off(self):
        with patch.dict(os.environ, {"MYAUTOPLAYER_DISABLE_AUDIO": "1"}):
            sound = SoundEffects()
        self.assertIsNone(sound._play_sound)

    def test_defaults_on_persists_setting_and_plays_existing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "assets"
            assets.mkdir()
            (assets / "sound-on.wav").write_bytes(b"on")
            (assets / "sound-off.wav").write_bytes(b"off")
            settings = root / "settings.json"
            settings.write_text('{"popup_enabled": true}', encoding="utf-8")
            played = []
            sound = SoundEffects(
                settings_path=settings,
                assets_root=assets,
                play_sound=lambda path, flags: played.append((Path(path).name, flags)),
            )

            self.assertTrue(sound.enabled)
            sound.play_started()
            sound.set_enabled(True)
            sound.play_started()
            sound.play_stopped()

            self.assertEqual(
                [name for name, _ in played],
                ["sound-on.wav", "sound-on.wav", "sound-off.wav"],
            )
            saved = json.loads(settings.read_text(encoding="utf-8"))
            self.assertTrue(saved["popup_enabled"])
            self.assertTrue(saved["sound_effects_enabled"])
            self.assertTrue(saved["sound_effects_default_on_v2"])

    def test_old_false_default_is_migrated_to_new_default_on(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "settings.json"
            settings.write_text('{"sound_effects_enabled": false}', encoding="utf-8")
            self.assertTrue(SoundEffects(settings_path=settings).enabled)
            settings.write_text(
                '{"sound_effects_enabled": false, "sound_effects_default_on_v2": true}',
                encoding="utf-8",
            )
            self.assertFalse(SoundEffects(settings_path=settings).enabled)

    def test_missing_asset_or_playback_failure_is_silent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sound = SoundEffects(
                settings_path=root / "settings.json",
                assets_root=root / "missing",
                play_sound=lambda *_: (_ for _ in ()).throw(OSError("no device")),
            )
            sound.set_enabled(True)
            sound.play_started()
            sound.play_stopped()


if __name__ == "__main__":
    unittest.main()
