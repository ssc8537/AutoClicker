import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from src.core.replay_history import (
    ReplayHistoryError,
    ReplayHistoryStore,
)


class ReplayHistoryStoreTests(unittest.TestCase):
    def _make_session(
        self,
        root: Path,
        *,
        label: str = "精彩连招",
        stamp: str = "20260722-090825",
        metadata: dict[str, object] | str | None = None,
        with_video: bool = True,
        with_subtitle: bool = True,
    ) -> Path:
        date = f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"
        session = root / date / f"{label}-{stamp}-recording"
        session.mkdir(parents=True)
        if with_video:
            (session / "raw.mp4").write_bytes(b"video")
        if with_subtitle:
            (session / "raw.ass").write_text("subtitle", encoding="utf-8")
        if metadata is None:
            metadata = {
                "saved_at": f"{date}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}.000",
                "actual_duration_ms": 65_200,
                "quality": "1080p",
                "requested_fps": 30,
                "encoder_mode": "gpu",
                "audio_track_count": 2,
                "event_count": 17,
            }
        if isinstance(metadata, str):
            (session / "metadata.json").write_text(metadata, encoding="utf-8")
        else:
            (session / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
            )
        return session

    def test_scan_reads_metadata_and_formats_a_complete_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = self._make_session(root)
            entries = ReplayHistoryStore(root).scan()
            subtitle_path = entries[0].subtitle_path
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.directory, session)
        self.assertEqual(entry.display_name, "精彩连招")
        self.assertEqual(entry.duration_text, "1:05")
        self.assertEqual(entry.video_format_text, "1080p / 30fps")
        self.assertEqual(entry.encoder, "GPU")
        self.assertEqual(entry.audio_text, "2 条")
        self.assertEqual(entry.event_count, 17)
        self.assertEqual(entry.status, "可播放")
        self.assertEqual(subtitle_path, session / "raw.ass")

    def test_latest_session_is_first_and_bad_metadata_is_still_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_session = self._make_session(
                root, label="旧记录", stamp="20260721-230000"
            )
            new_session = self._make_session(
                root,
                label="新记录",
                stamp="20260722-090000",
                metadata="{broken",
            )
            entries = ReplayHistoryStore(root).scan()
        self.assertEqual([entry.directory for entry in entries], [new_session, old_session])
        self.assertEqual(entries[0].display_name, "新记录")
        self.assertEqual(entries[0].status, "信息不完整")

    def test_unrecognised_directories_and_outside_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            (root / "notes").mkdir()
            (root / "2026-07-22" / "not-a-session").mkdir(parents=True)
            (root / "2026-07-22" / "not-a-session" / "readme.txt").write_text(
                "ignore", encoding="utf-8"
            )
            store = ReplayHistoryStore(root)
            self.assertEqual(store.scan(), [])
            valid = self._make_session(root)
            entry = store.scan()[0]
            outside_entry = replace(entry, directory=Path(outside))
            with self.assertRaises(ReplayHistoryError):
                store.move_to_recycle_bin(outside_entry)
            self.assertTrue(valid.is_dir())

    def test_in_progress_saving_directory_is_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saving = root / "2026-07-22" / ".精彩连招-20260722-090825-recording.saving"
            saving.mkdir(parents=True)
            (saving / "raw.mp4").write_bytes(b"partial")
            self.assertEqual(ReplayHistoryStore(root).scan(), [])

    def test_date_directory_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._make_session(root)
            date_directory = root / "2026-07-22"
            original_is_symlink = Path.is_symlink

            def report_date_directory_as_link(path: Path) -> bool:
                return path == date_directory or original_is_symlink(path)

            with patch.object(
                Path, "is_symlink", autospec=True, side_effect=report_date_directory_as_link
            ):
                self.assertEqual(ReplayHistoryStore(root).scan(), [])

    def test_delete_revalidates_and_uses_windows_recycle_bin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = self._make_session(root)
            store = ReplayHistoryStore(root)
            entry = store.scan()[0]
            with patch(
                "src.core.replay_history.move_path_to_windows_recycle_bin"
            ) as recycle:
                store.move_to_recycle_bin(entry)
            recycle.assert_called_once_with(session)
            self.assertTrue(session.is_dir())


if __name__ == "__main__":
    unittest.main()
