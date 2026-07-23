import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.core.native_replay import (
    NativeAudioPreviewController,
    NativeReplayController,
    _write_merge_plan,
    _wasapi_endpoint_id,
    native_replay_executable,
    normalise_replay_session_name,
)
from src.core.hotkey_manager import PhysicalInputEvent
from src.core.input_keys import physical_event_text, physical_input_name
from src.core.replay_settings import ReplaySettings


class NativeReplayControllerTests(unittest.TestCase):
    def test_thirty_minute_merge_plan_keeps_540_segment_paths_out_of_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            videos = [root / f"segment-{index:06}.mp4" for index in range(1, 181)]
            desktop = [root / f"desktop-{index:06}.mp4" for index in range(1, 181)]
            microphone = [root / f"microphone-{index:06}.mp4" for index in range(1, 181)]
            plan = root / "merge-plan.txt"
            output = root / "raw.mp4"
            _write_merge_plan(plan, output, videos, desktop, microphone)

            lines = plan.read_text(encoding="utf-8").splitlines()
            command = ["recorder.exe", "--merge-manifest", str(plan)]
            self.assertEqual(len(lines), 541)
            self.assertEqual(lines[0], f"output\t{output}")
            self.assertEqual(len([line for line in lines if line.startswith("video\t")]), 180)
            self.assertEqual(len([line for line in lines if line.startswith("desktop\t")]), 180)
            self.assertEqual(len([line for line in lines if line.startswith("microphone\t")]), 180)
            self.assertEqual(len(command), 3)

    def test_audio_preview_uses_native_level_only_mode_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "recorder.exe"
            executable.touch()
            process = Mock()
            process.poll.return_value = None
            process.wait.return_value = 0
            settings = ReplaySettings(
                Path(directory) / "captures",
                core_path=executable,
                microphone_device_id="selected-device",
                microphone_gain_percent=135,
            )
            with patch(
                "src.core.native_replay.subprocess.Popen", return_value=process
            ) as popen:
                preview = NativeAudioPreviewController()
                preview.start(settings)
                command = popen.call_args.args[0]
                self.assertIn("--audio-monitor", command)
                self.assertEqual(command[command.index("--audio-monitor") + 1], "true")
                self.assertEqual(
                    command[command.index("--microphone-device-id") + 1],
                    "selected-device",
                )
                preview._levels_file.write_text(
                    '{"desktop":42,"microphone":61}', encoding="utf-8"
                )
                self.assertEqual(preview.audio_levels(), (42, 61))
                stop_file = preview._stop_file
                self.assertEqual(preview.stop(), 0)
                self.assertTrue(stop_file is not None)
                process.wait.assert_called_once()

    def test_session_folder_name_validation(self):
        self.assertEqual(normalise_replay_session_name(" 秧秧完美连招 "), "秧秧完美连招")
        for invalid in ("", "CON", "bad/name", "bad:name"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                normalise_replay_session_name(invalid)

    def test_physical_key_names_follow_project_language(self):
        self.assertEqual(physical_input_name("1"), "大写 1")
        self.assertEqual(physical_input_name("e"), "大写 E")
        self.assertEqual(physical_input_name("mouse_back"), "侧键 1")
        self.assertEqual(
            physical_event_text("e", True, ("战技",)),
            "按下了战技（物理键：大写 E）",
        )

    def test_executable_lookup_fails_closed(self):
        with patch("src.core.native_replay.resource_root", return_value=Path("Z:/missing")), patch(
            "src.core.native_replay.application_root", return_value=Path("Z:/missing")
        ):
            self.assertIsNone(native_replay_executable())

    def test_qt_microphone_hex_id_is_decoded_for_wasapi(self):
        endpoint = "{0.0.1.00000000}.{388b056b-0d28-4630-843a-e5966372175c}"
        self.assertEqual(_wasapi_endpoint_id(endpoint.encode().hex()), endpoint)
        self.assertEqual(_wasapi_endpoint_id(endpoint), endpoint)

    def test_start_passes_explicit_encoder_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "recorder.exe"
            executable.touch()
            process = Mock()
            process.poll.return_value = None
            with patch("src.core.native_replay.native_replay_executable", return_value=executable), patch(
                "src.core.native_replay.subprocess.Popen", return_value=process
            ) as popen:
                controller = NativeReplayController()
                controller.start(ReplaySettings(root / "captures", 10, "720p", "cpu"))
            command = popen.call_args.args[0]
            self.assertEqual(command[command.index("--encoder") + 1], "cpu")
            self.assertEqual(command[command.index("--fps") + 1], "30")
            self.assertEqual(command[command.index("--monitor") + 1], "1")
            self.assertEqual(command[command.index("--record-microphone") + 1], "false")
            self.assertEqual(command[command.index("--microphone-gain-percent") + 1], "100")
            self.assertIn("--audio-manifest", command)
            self.assertIn("--audio-levels", command)
            self.assertNotIn("--process", command)
            self.assertNotIn("gpu", command)
            process.poll.return_value = 0
            controller.poll()

    def test_input_writer_records_global_edges_with_foreground_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "recorder.exe"
            executable.touch()
            process = Mock()
            process.poll.return_value = None
            with patch("src.core.native_replay.native_replay_executable", return_value=executable), patch(
                "src.core.native_replay.subprocess.Popen", return_value=process
            ), patch("src.core.native_replay._process_basename", side_effect=lambda pid: "Client-Win64-Shipping.exe" if pid == 7 else "notepad.exe"):
                controller = NativeReplayController()
                session = controller.start(ReplaySettings(root / "captures"))
                now = controller._session_monotonic_ns + 1_000_000
                controller.observe_input(PhysicalInputEvent("e", True, 69, now, 10, 7))
                controller.observe_input(PhysicalInputEvent("q", True, 81, now, 11, 8))
                process.poll.return_value = 0
                controller.poll()
            lines = session.events_jsonl.read_text(encoding="utf-8").splitlines()
            self.assertIn('"hotkey":"e"', lines[0])
            self.assertRegex(lines[0], r'"local_time":"\d{2}:\d{2}:\d{2}:\d{3}"')
            q_record = next(json.loads(line) for line in lines if '"hotkey":"q"' in line)
            self.assertEqual(q_record["delta_from_previous_event_ms"], 0.0)
            self.assertEqual(q_record["active_keys_after_event"], ["e", "q"])
            self.assertEqual(q_record["overlap_keys"], ["e"])
            self.assertEqual(q_record["overlap_count"], 1)
            self.assertTrue(session.events_csv.read_text(encoding="utf-8-sig").startswith("序号,本地时间,相对毫秒,距上一事件毫秒,"))
            self.assertTrue(session.events_jsonl.is_file())
            self.assertTrue(session.events_csv.is_file())
            self.assertFalse((session.directory / "raw.ass").exists())

    def test_repeat_down_is_not_written(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "recorder.exe"
            executable.touch()
            process = Mock()
            process.poll.return_value = None
            with patch("src.core.native_replay.native_replay_executable", return_value=executable), patch(
                "src.core.native_replay.subprocess.Popen", return_value=process
            ):
                controller = NativeReplayController()
                session = controller.start(ReplaySettings(root / "captures"))
                now = controller._session_monotonic_ns + 1_000_000
                controller.observe_input(PhysicalInputEvent("e", True, 69, now, 10, 7))
                controller.observe_input(PhysicalInputEvent("e", True, 69, now + 5_000_000, 10, 7))
                controller.observe_input(PhysicalInputEvent("e", False, 69, now + 25_000_000, 10, 7))
                process.poll.return_value = 0
                controller.poll()
            records = [
                line for line in session.events_jsonl.read_text(encoding="utf-8").splitlines()
                if '"sequence"' in line
            ]
            self.assertEqual(len(records), 2)

    def test_save_recent_exports_snapshot_without_stopping_buffer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "recorder.exe"
            executable.touch()
            process = Mock()
            process.poll.return_value = None
            settings = ReplaySettings(root / "captures", 5, "720p", "cpu", 15)
            merge_commands = []
            merge_plans = []

            def fake_merge(command, **_kwargs):
                merge_commands.append(command)
                plan = Path(command[command.index("--merge-manifest") + 1])
                lines = plan.read_text(encoding="utf-8").splitlines()
                merge_plans.append(lines)
                output = Path(next(line.split("\t", 1)[1] for line in lines if line.startswith("output\t")))
                output.touch()
                return SimpleNamespace(returncode=0, stdout="merge ok\n")

            with patch("src.core.native_replay.native_replay_executable", return_value=executable), patch(
                "src.core.native_replay.subprocess.Popen", return_value=process
            ), patch("src.core.native_replay.subprocess.run", side_effect=fake_merge):
                controller = NativeReplayController()
                buffer = controller.start(settings)
                now = controller._session_monotonic_ns + 1_000_000
                controller.observe_input(PhysicalInputEvent("e", True, 69, now, 10, 7))
                controller.observe_input(PhysicalInputEvent("e", False, 69, now + 25_000_000, 10, 7))
                start_qpc = controller._session_monotonic_ns // 100
                end_qpc = start_qpc + 10_000_000
                segment = buffer.segments_directory / "segment-000001.mp4"
                segment.write_bytes(b"fixture")
                manifest = [{
                    "index": 1,
                    "file": segment.name,
                    "start_qpc": start_qpc,
                    "end_qpc": end_qpc,
                }]
                desktop = buffer.segments_directory / "desktop-000001.mp4"
                desktop.write_bytes(b"audio fixture")
                audio_manifest = [{
                    "source": "desktop",
                    "index": 1,
                    "file": desktop.name,
                    "start_qpc": start_qpc,
                    "end_qpc": end_qpc,
                }]
                buffer.audio_levels.write_text(
                    '{"desktop":0,"microphone":0,'
                    '"desktop_discontinuities":2,"microphone_discontinuities":1}',
                    encoding="utf-8",
                )
                with patch.object(controller, "_force_rotate", return_value=1), patch.object(
                    controller, "_wait_for_manifest_index", return_value=manifest
                ), patch.object(
                    controller, "_wait_for_audio_manifest_indices", return_value=audio_manifest
                ):
                    saved = controller.save_recent(settings, "精彩连招", duration_minutes=5)
                self.assertTrue(controller.running)
                process.wait.assert_not_called()
                self.assertTrue(saved.raw_video.is_file())
                self.assertTrue(saved.events_jsonl.is_file())
                self.assertTrue(saved.input_subtitles.is_file())
                self.assertIn("大写 E", saved.input_subtitles.read_text(encoding="utf-8-sig"))
                self.assertEqual(merge_commands[0][1], "--merge-manifest")
                self.assertEqual(len(merge_commands[0]), 3)
                self.assertTrue(any(line.startswith("video\t") for line in merge_plans[0]))
                self.assertTrue(any(line.startswith("desktop\t") for line in merge_plans[0]))
                self.assertFalse(any(line.startswith("microphone\t") for line in merge_plans[0]))
                saved_metadata = json.loads(saved.metadata.read_text(encoding="utf-8"))
                self.assertEqual(saved_metadata["desktop_gain_percent"], 150)
                self.assertEqual(
                    saved_metadata["desktop_audio_discontinuities_recovered"], 2
                )
                self.assertEqual(
                    saved_metadata["microphone_audio_discontinuities_recovered"], 1
                )
                process.poll.return_value = 0
                controller.poll()

    def test_audio_levels_reads_bounded_pcm_peaks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "recorder.exe"
            executable.touch()
            process = Mock()
            process.poll.return_value = None
            with patch("src.core.native_replay.native_replay_executable", return_value=executable), patch(
                "src.core.native_replay.subprocess.Popen", return_value=process
            ):
                controller = NativeReplayController()
                buffer = controller.start(ReplaySettings(root / "captures"))
                buffer.audio_levels.write_text(
                    '{"desktop":135,"microphone":27}', encoding="utf-8"
                )
                self.assertEqual(controller.audio_levels(), (100, 27))
                process.poll.return_value = 0
                controller.poll()

    def test_formal_sibling_core_is_auto_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = root / "native-replay" / "myautoplayer-native-replay.exe"
            core.parent.mkdir()
            core.touch()
            with patch("src.core.native_replay.application_root", return_value=root), patch(
                "src.core.native_replay.resource_root", return_value=Path("Z:/internal")
            ):
                self.assertEqual(native_replay_executable(), core.resolve())


if __name__ == "__main__":
    unittest.main()
