import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from main import (
    _HotkeyDispatcher,
    _INSTRUCTION_TEXT,
    MainWindow,
    global_status_notification,
    show_startup_window,
)


class _FakeLabel:
    def __init__(self):
        self.text = None
        self.style = None

    def setText(self, value):
        self.text = value

    def setStyleSheet(self, value):
        self.style = value


class _FakeOsd:
    def __init__(self):
        self.calls = []

    def show_notification(self, text, success):
        self.calls.append((text, success))


class _FakePlayer:
    def __init__(self):
        self.stop_calls = 0

    def stop(self):
        self.stop_calls += 1

    def is_running(self):
        return True


class _FakeSoundEffects:
    def __init__(self):
        self.calls = []

    def play_started(self):
        self.calls.append("started")

    def play_stopped(self):
        self.calls.append("stopped")


class _FakeWindow:
    def __init__(self):
        self.calls = []

    def show(self):
        self.calls.append("show")

    def raise_(self):
        self.calls.append("raise")

    def activateWindow(self):
        self.calls.append("activate")


class MainStatusTests(unittest.TestCase):
    def test_startup_window_is_shown_raised_and_activated(self):
        window = _FakeWindow()
        show_startup_window(window)
        self.assertEqual(window.calls, ["show", "raise", "activate"])

    def test_instruction_text_has_real_newlines(self):
        self.assertIn("\n", _INSTRUCTION_TEXT)
        self.assertNotIn("\\\\n", _INSTRUCTION_TEXT)

    def test_global_status_messages(self):
        self.assertEqual(global_status_notification(False), ("全局脚本已就绪", True))
        self.assertEqual(global_status_notification(True), ("全局脚本已禁用", False))

    def test_global_toggle_updates_label_and_osd(self):
        sounds = _FakeSoundEffects()
        target = SimpleNamespace(
            _status_label=_FakeLabel(), _osd_popup=_FakeOsd(), _sound_effects=sounds
        )
        _HotkeyDispatcher._apply_global_status(target, False)
        self.assertEqual(target._status_label.text, "● 热键已启用")
        self.assertEqual(target._osd_popup.calls, [("全局脚本已就绪", True)])
        _HotkeyDispatcher._apply_global_status(target, True)
        self.assertEqual(target._status_label.text, "● 热键已禁用")
        self.assertEqual(target._osd_popup.calls[-1], ("全局脚本已禁用", False))
        self.assertEqual(sounds.calls, ["started", "stopped"])

    def test_macro_start_and_stop_do_not_play_global_toggle_sounds(self):
        sounds = _FakeSoundEffects()
        target = SimpleNamespace(
            _players={"a": object()}, _running_names={"a": "goodbye"}, _osd_popup=_FakeOsd(),
            _sound_effects=sounds, _on_natural_finish=None,
            _player_generations={"a": 1}, _stop_lock=threading.RLock(),
            _pending_starts={}, _pending_stop_generations={},
        )
        _HotkeyDispatcher._on_player_finished(target, "a", 1)
        self.assertEqual(sounds.calls, [])

    def test_mouse_release_stop_requests_player_stop_before_qt_queue_delivery(self):
        player = _FakePlayer()
        target = SimpleNamespace(
            _players={"side": player}, _stop_lock=threading.RLock(),
            _pending_stop_generations={}, _pending_starts={},
            f9_stop_signal=SimpleNamespace(emit=lambda *_: None),
        )
        _HotkeyDispatcher.on_macro_stop_hotkey(target, "side", 2)
        self.assertEqual(player.stop_calls, 1)

    def test_hook_thread_only_queues_path_and_never_loads_macro(self):
        emitted = []
        target = SimpleNamespace(
            macro_start_signal=SimpleNamespace(emit=lambda *args: emitted.append(args))
        )
        path = Path("hello_world.py")
        with patch("main.load_python_macro") as load:
            _HotkeyDispatcher.on_macro_hotkey(target, path, "macro", 7)
        load.assert_not_called()
        self.assertEqual(emitted, [(path, "macro", 7)])

    def test_duplicate_file_watcher_snapshot_does_not_rebuild_bindings(self):
        class Manager:
            def __init__(self):
                self.registered = []
                self.unregistered = []
                self.clear_calls = 0

            def register(self, *args, **kwargs):
                self.registered.append((args, kwargs))

            def unregister(self, binding_id):
                self.unregistered.append(binding_id)

            def clear_pending_events(self):
                self.clear_calls += 1
                return 0

        manager = Manager()
        entry = SimpleNamespace(
            valid=True,
            path=Path("hello_world.py"),
            macro=SimpleNamespace(enabled=True, hotkey="mouse_back", mode="down"),
        )
        target = SimpleNamespace(
            _hotkey_mgr=manager,
            _dispatcher=SimpleNamespace(
                on_macro_hotkey=lambda *_: None,
                on_macro_stop_hotkey=lambda *_: None,
            ),
            _macro_entries=[entry],
            _global_hotkey="backquote",
        )
        MainWindow._configure_independent_hotkeys(target)
        MainWindow._configure_independent_hotkeys(target)
        self.assertEqual(len(manager.registered), 1)
        self.assertEqual(manager.clear_calls, 1)

    def test_stop_osd_uses_the_macro_name_cached_at_start(self):
        player = _FakePlayer()
        target = SimpleNamespace(
            _players={"a": player},
            _stop_lock=threading.RLock(),
            _pending_stop_generations={},
            _pending_starts={},
            _running_names={"a": "新宏6"},
            _osd_popup=_FakeOsd(),
        )
        _HotkeyDispatcher._stop_f9(target, "a", 2)
        self.assertEqual(player.stop_calls, 1)

    def test_natural_finish_keeps_the_started_macro_name_after_selection_changes(self):
        target = SimpleNamespace(
            _on_natural_finish=None,
            _players={"a": object()},
            _player_generations={"a": 1},
            _running_names={"a": "goodbye"},
            _osd_popup=_FakeOsd(),
            _stop_lock=threading.RLock(),
            _pending_starts={},
            _pending_stop_generations={},
        )
        _HotkeyDispatcher._on_player_finished(target, "a", 1)
        self.assertEqual(target._osd_popup.calls, [("goodbye 宏已停止", False)])
        self.assertEqual(target._running_names, {})


if __name__ == "__main__":
    unittest.main()
