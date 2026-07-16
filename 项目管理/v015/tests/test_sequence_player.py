import threading
import time
import unittest

from src.core.sequence_player import KeyTapStep, SequencePlayer


class SequencePlayerTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.finished = threading.Event()
        self.player = SequencePlayer(
            press=lambda key: self.events.append(("down", key)),
            release=lambda key: self.events.append(("up", key)),
            on_finished=self.finished.set,
        )

    def test_plays_requested_finite_count_in_order(self):
        steps = (KeyTapStep("h", 1, 0), KeyTapStep("i", 1, 0))
        self.assertTrue(self.player.play(steps, count=2, speed=1.0))
        self.player.join(1.0)
        self.assertEqual(
            self.events,
            [("down", "h"), ("up", "h"), ("down", "i"), ("up", "i")] * 2,
        )
        self.assertTrue(self.finished.is_set())

    def test_stop_during_hold_releases_key(self):
        self.assertTrue(self.player.play((KeyTapStep("h", 5000, 0),), 1, 1.0))
        deadline = time.monotonic() + 1.0
        while ("down", "h") not in self.events and time.monotonic() < deadline:
            time.sleep(0.005)
        self.player.stop()
        self.player.join(1.0)
        self.assertEqual(self.events, [("down", "h"), ("up", "h")])

    def test_stop_during_delay_prevents_next_step(self):
        steps = (KeyTapStep("h", 1, 5000), KeyTapStep("i", 1, 0))
        self.assertTrue(self.player.play(steps, 1, 1.0))
        deadline = time.monotonic() + 1.0
        while ("up", "h") not in self.events and time.monotonic() < deadline:
            time.sleep(0.005)
        self.player.stop()
        self.player.join(1.0)
        self.assertEqual(self.events, [("down", "h"), ("up", "h")])

    def test_rejects_parallel_start(self):
        step = (KeyTapStep("h", 5000, 0),)
        self.assertTrue(self.player.play(step, 1, 1.0))
        self.assertFalse(self.player.play(step, 1, 1.0))
        self.player.stop()
        self.player.join(1.0)

    def test_speed_scales_only_release_delay(self):
        self.assertEqual(SequencePlayer.delay_seconds(100, 2.0), 0.05)
        self.assertEqual(SequencePlayer.delay_seconds(100, 0.5), 0.2)


if __name__ == "__main__":
    unittest.main()
