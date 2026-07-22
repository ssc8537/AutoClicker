import os
import unittest
from uuid import uuid4

from src.utils.single_instance import SingleInstanceGuard


@unittest.skipUnless(os.name == "nt", "Windows named mutex only")
class SingleInstanceTests(unittest.TestCase):
    def test_only_one_guard_can_own_the_same_name_and_release_restores_access(self):
        name = rf"Local\MyAutoPlayer.tests.{os.getpid()}.{uuid4().hex}"
        first = SingleInstanceGuard(name)
        second = SingleInstanceGuard(name)
        third = SingleInstanceGuard(name)
        try:
            self.assertTrue(first.acquire())
            self.assertFalse(second.acquire())
            first.release()
            self.assertTrue(third.acquire())
        finally:
            first.release()
            second.release()
            third.release()

    def test_second_launch_notifies_the_running_instance(self):
        name = rf"Local\MyAutoPlayer.tests.activate.{os.getpid()}.{uuid4().hex}"
        first = SingleInstanceGuard(name)
        second = SingleInstanceGuard(name)
        try:
            self.assertTrue(first.acquire())
            self.assertFalse(second.acquire())
            self.assertTrue(first.consume_activation_request())
            self.assertFalse(first.consume_activation_request())
        finally:
            first.release()
            second.release()


if __name__ == "__main__":
    unittest.main()
