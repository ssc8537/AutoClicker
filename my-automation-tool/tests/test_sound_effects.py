import json
import tempfile
import unittest
from pathlib import Path

from src.ui.sound_effects import SoundEffects


class SoundEffectsTests(unittest.TestCase):
    def test_defaults_off_persists_setting_and_plays_two_existing_assets(self):
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

            self.assertFalse(sound.enabled)
            sound.play_started()
            self.assertEqual(played, [])
            sound.set_enabled(True)
            sound.play_started()
            sound.play_stopped()

            self.assertEqual([name for name, _ in played], ["sound-on.wav", "sound-off.wav"])
            saved = json.loads(settings.read_text(encoding="utf-8"))
            self.assertTrue(saved["popup_enabled"])
            self.assertTrue(saved["sound_effects_enabled"])

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
