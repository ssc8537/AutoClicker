import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from src.utils import app_paths


class AppPathsTests(unittest.TestCase):
    def test_source_paths_keep_the_existing_project_layout(self):
        with patch.object(app_paths.sys, "frozen", False, create=True):
            root = app_paths.application_root()
        self.assertEqual(root, Path(__file__).resolve().parents[1])
        self.assertEqual(app_paths.macro_root(), root / "macros")
        self.assertEqual(app_paths.config_root(), root / "config")
        self.assertEqual(app_paths.log_root(), root / "logs")

    def test_frozen_paths_are_next_to_the_executable_not_meipass(self):
        executable = Path("C:/Portable/MyAutoPlayer/MyAutoPlayer.exe")
        meipass = Path("C:/Users/test/AppData/Local/Temp/_MEI123")
        with (
            patch.object(app_paths.sys, "frozen", True, create=True),
            patch.object(app_paths.sys, "executable", str(executable)),
            patch.object(app_paths.sys, "_MEIPASS", str(meipass), create=True),
        ):
            self.assertEqual(app_paths.application_root(), executable.parent)
            self.assertEqual(app_paths.macro_root(), executable.parent / "macros")
            self.assertEqual(app_paths.config_root(), executable.parent / "config")
            self.assertEqual(app_paths.log_root(), executable.parent / "logs")
            self.assertEqual(app_paths.resource_root(), meipass)
