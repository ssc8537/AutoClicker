import json
import tempfile
import unittest
from pathlib import Path

from src.ui.appearance import (
    AppearanceSettings,
    AppearanceSettingsStore,
    GALLERY_LAYOUT,
    SAKURA_THEME,
)


class AppearanceSettingsTests(unittest.TestCase):
    def test_missing_invalid_and_legacy_values_migrate_to_sakura_gallery(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            store = AppearanceSettingsStore(path)
            self.assertEqual(store.load(), AppearanceSettings())
            path.write_text(
                json.dumps({"ui_theme": "classic_pink", "ui_layout": "classic_tabs"}),
                encoding="utf-8",
            )
            loaded = store.load()
            self.assertEqual(loaded.theme, SAKURA_THEME)
            self.assertEqual(loaded.layout, GALLERY_LAYOUT)

    def test_save_round_trip_preserves_unrelated_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(
                json.dumps({"popup_enabled": False, "sound_enabled": True}),
                encoding="utf-8",
            )
            store = AppearanceSettingsStore(path)
            expected = AppearanceSettings(
                theme=SAKURA_THEME, layout=GALLERY_LAYOUT
            )
            store.save(expected)
            self.assertEqual(store.load(), expected)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(saved["popup_enabled"])
            self.assertTrue(saved["sound_enabled"])


if __name__ == "__main__":
    unittest.main()
