import threading
import time
import unittest

from src.core.sequence_player import SequencePlayer


class SequencePlayerTests(unittest.TestCase):
    def test_plays_requested_finite_count(self):
        calls = []
        finished = threading.Event()
        player = SequencePlayer(on_finished=finished.set)
        self.assertTrue(player.play(lambda _: calls.append("run") or True, count=2))
        player.join(1.0)
        self.assertEqual(calls, ["run", "run"])
        self.assertTrue(finished.is_set())

    def test_stop_prevents_next_round(self):
        started = threading.Event()
        player = SequencePlayer()

        def run_once(stop_event):
            started.set()
            return not stop_event.wait(5.0)

        self.assertTrue(player.play(run_once, count=0))
        self.assertTrue(started.wait(1.0))
        player.stop()
        player.join(1.0)
        self.assertFalse(player.is_running())

    def test_rejects_parallel_start(self):
        player = SequencePlayer()
        self.assertTrue(player.play(lambda event: not event.wait(5.0), count=1))
        self.assertFalse(player.play(lambda _: True, count=1))
        player.stop()
        player.join(1.0)


if __name__ == "__main__":
    unittest.main()
