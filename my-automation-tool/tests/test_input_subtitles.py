import tempfile
import unittest
from pathlib import Path

from src.core.input_subtitles import write_input_subtitles


class InputSubtitleTests(unittest.TestCase):
    def test_two_line_cards_show_key_hold_and_release_milliseconds(self):
        records = [
            {"state": "down", "hotkey": "e", "physical_name": "大写 E", "relative_ms": 100.0},
            {"state": "up", "hotkey": "e", "physical_name": "大写 E", "relative_ms": 150.0, "held_ms": 50.0},
            {"state": "down", "hotkey": "e", "physical_name": "大写 E", "relative_ms": 219.0},
            {"state": "up", "hotkey": "e", "physical_name": "大写 E", "relative_ms": 239.0, "held_ms": 20.0},
        ]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "raw.ass"
            srt_target = Path(directory) / "input_subtitles.srt"
            count = write_input_subtitles(
                target, records, session_end_ms=300.0, srt_target=srt_target
            )
            text = target.read_text(encoding="utf-8-sig")
            srt = srt_target.read_text(encoding="utf-8-sig")

        self.assertEqual(count, 2)
        self.assertEqual(text.count("Dialogue:"), 4)
        self.assertIn(r"大写 E\N", text)
        self.assertIn("按键：大写 E", text)
        self.assertIn("按下 50.0 ms  ·  分开 69.0 ms", text)
        self.assertIn("按下 20.0 ms  ·  分开 61.0 ms（至录像结束）", text)
        self.assertIn("00:00:00,100 --> 00:00:00,220", srt)
        self.assertIn("按键：大写 E\n按下 50.0 ms  ·  分开 69.0 ms", srt)
        self.assertIn(r"\p1\1c&H006F5A7D&\1a&H40&", text)
        self.assertIn(r"\bord6\shad2", text)

    def test_overlapping_keys_keep_independent_cards_and_unreleased_state(self):
        records = [
            {"state": "down", "hotkey": "1", "physical_name": "大写 1", "relative_ms": 0.0},
            {"state": "down", "hotkey": "q", "physical_name": "大写 Q", "relative_ms": 10.0},
            {"state": "up", "hotkey": "1", "physical_name": "大写 1", "relative_ms": 50.0, "held_ms": 50.0},
        ]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "input_subtitles.ass"
            count = write_input_subtitles(target, records, session_end_ms=100.0)
            text = target.read_text(encoding="utf-8-sig")

        self.assertEqual(count, 2)
        self.assertLess(text.index("大写 1"), text.index("大写 Q"))
        self.assertIn("录像结束仍按住", text)
        self.assertEqual(text.count(r"\an8\pos(960,"), 2)
        self.assertNotIn(r"\pos(960,855)", text)
        self.assertIn("按键：大写 1", text)
        self.assertIn("按键：大写 Q", text)

    def test_empty_timeline_still_produces_valid_ass(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "raw.ass"
            count = write_input_subtitles(target, [], session_end_ms=0.0)
            text = target.read_text(encoding="utf-8-sig")
        self.assertEqual(count, 0)
        self.assertIn("[V4+ Styles]", text)
        self.assertNotIn("Dialogue:", text)

    def test_rapid_combo_snapshots_do_not_overlap_or_hide_detail_lines(self):
        records = []
        for index, key in enumerate(("e", "q", "e", "q", "e", "w", "q", "e", "q")):
            down = 100.0 + index * 50.0
            records.extend(
                [
                    {"state": "down", "hotkey": key, "physical_name": f"大写 {key.upper()}", "relative_ms": down},
                    {"state": "up", "hotkey": key, "physical_name": f"大写 {key.upper()}", "relative_ms": down + 20.0, "held_ms": 20.0},
                ]
            )
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "raw.ass"
            write_input_subtitles(target, records, session_end_ms=700.0)
            dialogues = [
                line for line in target.read_text(encoding="utf-8-sig").splitlines()
                if line.startswith("Dialogue: 1,")
            ]

        self.assertEqual(len(dialogues), 9)
        self.assertTrue(all("按键：" in line for line in dialogues))
        self.assertTrue(all("按下 " in line and "分开 " in line for line in dialogues))
        self.assertTrue(any(r"\pos(960,582)" in line for line in dialogues))
        ranges = [line.split(",", 3)[1:3] for line in dialogues]
        for previous, current in zip(ranges, ranges[1:]):
            self.assertLessEqual(_ass_seconds(previous[1]), _ass_seconds(current[0]))

    def test_events_in_same_ass_centisecond_share_one_panel(self):
        records = [
            {"state": "down", "hotkey": "h", "physical_name": "大写 H", "relative_ms": 100.1},
            {"state": "up", "hotkey": "h", "physical_name": "大写 H", "relative_ms": 101.0, "held_ms": 0.9},
            {"state": "down", "hotkey": "c", "physical_name": "大写 C", "relative_ms": 105.8},
            {"state": "up", "hotkey": "c", "physical_name": "大写 C", "relative_ms": 108.0, "held_ms": 2.2},
        ]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "raw.ass"
            write_input_subtitles(target, records, session_end_ms=300.0)
            text = target.read_text(encoding="utf-8-sig")
            text_dialogues = [
                line for line in text.splitlines() if line.startswith("Dialogue: 1,")
            ]

        self.assertEqual(len(text_dialogues), 1)
        self.assertIn("按键：大写 H", text_dialogues[0])
        self.assertIn("按键：大写 C", text_dialogues[0])
        self.assertIn("Dialogue: 0,", text)
        self.assertIn(r"\p1", text)


def _ass_seconds(value: str) -> float:
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


if __name__ == "__main__":
    unittest.main()
