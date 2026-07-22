import unittest
from pathlib import Path


class ReleaseHygieneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool_root = Path(__file__).resolve().parents[1]
        cls.repository_root = cls.tool_root.parent

    def test_runtime_machine_state_is_ignored_by_git(self):
        ignore = (self.repository_root / ".gitignore").read_text(encoding="utf-8")
        for relative in (
            "my-automation-tool/config/replay_settings.json",
            "my-automation-tool/config/key_monitor.json",
            "my-automation-tool/config/ai_prompt.complete.md",
            "my-automation-tool/native-replay/.cargo/",
        ):
            with self.subTest(relative=relative):
                self.assertIn(relative, ignore)

    def test_portable_build_removes_runtime_machine_state(self):
        build_script = (self.tool_root / "scripts" / "build_windows.ps1").read_text(
            encoding="utf-8"
        )
        for filename in (
            "replay_settings.json",
            "key_monitor.json",
            "ai_prompt.complete.md",
        ):
            with self.subTest(filename=filename):
                self.assertIn(filename, build_script)
        self.assertIn("Remove-Item -LiteralPath $runtimeState -Force", build_script)


if __name__ == "__main__":
    unittest.main()
