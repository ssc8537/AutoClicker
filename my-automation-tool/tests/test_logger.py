import logging
import os
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from src.utils.logger import (
    DailyDirectoryRotatingFileHandler,
    clear_logs_older_than,
    daily_log_path,
    migrate_legacy_logs,
)


class DailyLogTests(unittest.TestCase):
    def test_each_record_is_written_into_its_date_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            handler = DailyDirectoryRotatingFileHandler(root)
            handler.setFormatter(logging.Formatter("%(message)s"))
            first = logging.LogRecord("test", logging.INFO, __file__, 1, "第一天", (), None)
            first.created = datetime(2026, 7, 20, 23, 59).timestamp()
            second = logging.LogRecord("test", logging.INFO, __file__, 1, "第二天", (), None)
            second.created = datetime(2026, 7, 21, 0, 1).timestamp()
            handler.emit(first)
            handler.emit(second)
            handler.close()
            self.assertEqual(
                daily_log_path(date(2026, 7, 20), root).read_text(encoding="utf-8").strip(),
                "第一天",
            )
            self.assertEqual(
                daily_log_path(date(2026, 7, 21), root).read_text(encoding="utf-8").strip(),
                "第二天",
            )

    def test_legacy_root_log_moves_to_its_modified_date_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "app.log"
            legacy.write_text("旧版日志", encoding="utf-8")
            stamp = datetime(2026, 7, 20, 20, 30).timestamp()
            os.utime(legacy, (stamp, stamp))
            current = daily_log_path(date(2026, 7, 20), root)
            current.parent.mkdir(parents=True)
            current.write_text("新版日志", encoding="utf-8")
            migrated = migrate_legacy_logs(log_dir=root)
            self.assertFalse(legacy.exists())
            self.assertEqual(migrated, [current.parent / "legacy-app.log"])
            self.assertEqual(migrated[0].read_text(encoding="utf-8"), "旧版日志")
            self.assertEqual(current.read_text(encoding="utf-8"), "新版日志")

    def test_cleanup_offers_one_five_and_thirty_day_boundaries(self):
        today = date(2026, 7, 20)
        cases = (
            (1, date(2026, 7, 19), date(2026, 7, 20)),
            (5, date(2026, 7, 15), date(2026, 7, 16)),
            (30, date(2026, 6, 20), date(2026, 6, 21)),
        )
        for retention, removed_day, preserved_day in cases:
            with self.subTest(retention=retention), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                removed = daily_log_path(removed_day, root)
                preserved = daily_log_path(preserved_day, root)
                current = daily_log_path(today, root)
                unknown = root / "用户保留" / "note.txt"
                for path in (removed, preserved, current, unknown):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("x", encoding="utf-8")
                count = clear_logs_older_than(retention, log_dir=root, today=today)
                self.assertEqual(count, 1)
                self.assertFalse(removed.parent.exists())
                self.assertTrue(preserved.exists())
                self.assertTrue(current.exists())
                self.assertTrue(unknown.exists())


if __name__ == "__main__":
    unittest.main()
