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


if __name__ == "__main__":
    unittest.main()
