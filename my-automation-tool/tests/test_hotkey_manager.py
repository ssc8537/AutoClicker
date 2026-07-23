import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.core.hotkey_manager import HotkeyManager, PhysicalInputEvent, TriggerMode
from src.core.input_simulator import INPUT_EVENT_MARKER


class HotkeyManagerTests(unittest.TestCase):
    def test_global_automation_is_enabled_by_default(self):
        manager = HotkeyManager()
        self.assertFalse(manager.global_disabled)
        self.assertTrue(manager.toggle_global_disabled())

    def make_handler(self, mode, stop_on_release=True):
        started = []
        stopped = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register(
            "f9", lambda _generation: started.append("start"), mode,
            lambda _generation: stopped.append("stop"),
            stop_on_release=stop_on_release,
        )
        return manager, manager._make_handler("f9"), started, stopped

    def event(self, event_type):
        return SimpleNamespace(event_type=event_type)

    def test_background_window_rectangle_never_suppresses_game_mouse_input(self):
        manager = HotkeyManager(main_window_hwnd=123)
        with patch.object(
            manager, "_main_hwnd", 123
        ), patch("src.core.hotkey_manager.ctypes.windll.user32.GetForegroundWindow", return_value=456), patch(
            "src.core.hotkey_manager.ctypes.windll.user32.GetWindowThreadProcessId"
        ) as process_id:
            def report_other_process(_hwnd, pointer):
                pointer._obj.value = 999999
                return 1

            process_id.side_effect = report_other_process
            self.assertFalse(manager.is_mouse_over_window())

    def test_foreground_own_window_still_suppresses_clicks_inside_its_rectangle(self):
        manager = HotkeyManager(main_window_hwnd=123)

        def report_current_process(_hwnd, pointer):
            import os
            pointer._obj.value = os.getpid()
            return 1

        def report_cursor(pointer):
            pointer._obj.x = 50
            pointer._obj.y = 50
            return 1

        def report_rect(_hwnd, pointer):
            pointer._obj.left = 0
            pointer._obj.top = 0
            pointer._obj.right = 100
            pointer._obj.bottom = 100
            return 1

        with patch(
            "src.core.hotkey_manager.ctypes.windll.user32.GetForegroundWindow", return_value=123
        ), patch(
            "src.core.hotkey_manager.ctypes.windll.user32.GetWindowThreadProcessId",
            side_effect=report_current_process,
        ), patch(
            "src.core.hotkey_manager.ctypes.windll.user32.GetCursorPos",
            side_effect=report_cursor,
        ), patch(
            "src.core.hotkey_manager.ctypes.windll.user32.GetWindowRect",
            side_effect=report_rect,
        ):
            self.assertTrue(manager.is_mouse_over_window())

    def test_down_starts_on_press_and_stops_on_release(self):
        _, handler, started, stopped = self.make_handler(TriggerMode.DOWN)
        handler(self.event("down"))
        handler(self.event("up"))
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, ["stop"])

    def test_temporary_input_suppresses_new_triggers_but_keeps_release_safe(self):
        manager, _handler, started, stopped = self.make_handler(TriggerMode.DOWN)
        manager.set_trigger_suppressed(True)
        manager._dispatch_physical_event("f9", True)
        manager._dispatch_physical_event("f9", False)
        self.assertEqual(started, [])
        self.assertEqual(stopped, ["stop"])

        manager.set_trigger_suppressed(False)
        manager._dispatch_physical_event("f9", True)
        self.assertEqual(started, ["start"])
        manager.set_trigger_suppressed(True)
        manager._dispatch_physical_event("f9", False)
        self.assertEqual(stopped, ["stop", "stop"])

    def test_temporary_input_suppresses_global_toggle_status(self):
        manager = HotkeyManager()
        manager.set_global_disable_key("f9")
        manager.set_trigger_suppressed(True)
        manager._dispatch_physical_event("f9", True)
        manager._dispatch_physical_event("f9", False)
        self.assertFalse(manager.global_disabled)

    def test_down_release_is_an_idempotent_stop_even_for_finite_runs(self):
        _, handler, started, stopped = self.make_handler(TriggerMode.DOWN)
        handler(self.event("down"))
        handler(self.event("up"))
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, ["stop"])

    def test_switch_toggles_on_each_physical_press(self):
        _, handler, started, stopped = self.make_handler(TriggerMode.SWITCH)
        handler(self.event("down"))
        handler(self.event("up"))
        handler(self.event("down"))
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, ["stop"])

    def test_second_hotkey_can_start_while_first_execution_is_active(self):
        started = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register("f1", lambda _generation: started.append("f1"), TriggerMode.DOWN)
        manager.register("f3", lambda _generation: started.append("f3"), TriggerMode.DOWN)
        first = manager._make_handler("f1")
        second = manager._make_handler("f3")
        first(self.event("down"))
        second(self.event("down"))
        second(self.event("up"))
        self.assertEqual(started, ["f1", "f3"])
        manager.mark_finished("f1")
        second(self.event("down"))
        self.assertEqual(started, ["f1", "f3", "f3"])

    def test_side_button_down_mode_stops_immediately_on_release(self):
        started = []
        stopped = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register(
            "mouse_back", lambda _generation: started.append("start"), TriggerMode.DOWN,
            lambda _generation: stopped.append("stop"), binding_id="side",
        )
        manager._dispatch_physical_event("mouse_back", True)
        manager._dispatch_physical_event("mouse_back", False)
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, ["stop"])

    def test_raw_xbutton_edges_are_read_and_only_own_marker_is_ignored(self):
        manager = HotkeyManager()
        queued = []
        manager._queue_physical_event = lambda key, pressed: queued.append((key, pressed))
        manager._on_windows_mouse_event(
            0x020B, SimpleNamespace(mouseData=1 << 16, dwExtraInfo=None, flags=1)
        )
        manager._on_windows_mouse_event(
            0x020C, SimpleNamespace(mouseData=1 << 16, dwExtraInfo=None, flags=1)
        )
        manager._on_windows_mouse_event(
            0x020B,
            SimpleNamespace(mouseData=1 << 16, dwExtraInfo=INPUT_EVENT_MARKER, flags=1),
        )
        self.assertEqual(queued, [("mouse_back", True), ("mouse_back", False)])

    def test_raw_windows_vk_is_stable_under_ime_and_ignores_processkey(self):
        manager = HotkeyManager()
        queued = []
        manager._queue_physical_event = lambda key, pressed: queued.append((key, pressed))
        manager._on_windows_keyboard_event(
            0x0100, SimpleNamespace(vkCode=0x41, flags=0, dwExtraInfo=None)
        )
        manager._on_windows_keyboard_event(
            0x0101, SimpleNamespace(vkCode=0x41, flags=0, dwExtraInfo=None)
        )
        manager._on_windows_keyboard_event(
            0x0100, SimpleNamespace(vkCode=0xE5, flags=0, dwExtraInfo=0)
        )
        # 案例只过滤自己的 dwExtraInfo；第三方/驱动 injected 物理键仍可触发。
        manager._on_windows_keyboard_event(
            0x0100, SimpleNamespace(vkCode=0x42, flags=0x10, dwExtraInfo=0)
        )
        manager._on_windows_keyboard_event(
            0x0100,
            SimpleNamespace(vkCode=0x43, flags=0x10, dwExtraInfo=INPUT_EVENT_MARKER),
        )
        self.assertEqual(queued, [("a", True), ("a", False), ("b", True)])

    def test_old_finish_generation_cannot_clear_a_new_switch_run(self):
        started = []
        stopped = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register(
            "f9", lambda generation: started.append(generation), TriggerMode.SWITCH,
            lambda generation: stopped.append(generation), binding_id="macro",
        )
        handler = manager._make_handler("f9")
        handler(self.event("down"))
        handler(self.event("up"))
        handler(self.event("down"))
        handler(self.event("up"))
        handler(self.event("down"))
        manager.mark_finished("macro", started[0])
        handler(self.event("up"))
        handler(self.event("down"))
        self.assertEqual(started, [1, 3])
        self.assertEqual(stopped, [2, 4])

    def test_reconfiguration_clears_old_edges_without_waiting(self):
        manager = HotkeyManager()
        manager._pressed_hotkeys.add("mouse_back")
        manager._event_queue.put_nowait(("mouse_back", True, 0))
        manager._event_queue.put_nowait(("mouse_back", False, 0))
        self.assertEqual(manager.clear_pending_events(), 2)
        self.assertEqual(manager._pressed_hotkeys, set())
        self.assertTrue(manager._event_queue.empty())

    def test_generation_never_resets_across_disable_and_reregister(self):
        started = []
        stopped = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register(
            "mouse_back", started.append, TriggerMode.DOWN, stopped.append,
            binding_id="macro",
        )
        for _ in range(20):
            manager._dispatch_physical_event("mouse_back", True)
            manager._dispatch_physical_event("mouse_back", False)
        self.assertEqual(started[-1], 39)
        self.assertEqual(stopped[-1], 40)

        manager.unregister("macro")
        manager.register(
            "mouse_back", started.append, TriggerMode.DOWN, stopped.append,
            binding_id="macro",
        )
        manager._dispatch_physical_event("mouse_back", True)
        self.assertEqual(started[-1], 41)

    def test_unmatched_release_still_stops_a_down_binding(self):
        stopped = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.register(
            "mouse_back", lambda _generation: None, TriggerMode.DOWN,
            stopped.append, binding_id="macro",
        )
        manager._pressed_hotkeys.clear()
        manager._dispatch_physical_event("mouse_back", False)
        self.assertEqual(stopped, [1])

    def test_one_hundred_fast_side_button_down_up_pairs_never_stick(self):
        started = []
        stopped = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register(
            "mouse_back", started.append, TriggerMode.DOWN, stopped.append,
            binding_id="macro",
        )
        for _ in range(100):
            manager._dispatch_physical_event("mouse_back", True)
            manager._dispatch_physical_event("mouse_back", False)
        self.assertEqual(len(started), 100)
        self.assertEqual(len(stopped), 100)
        self.assertFalse(manager._bindings_by_id["macro"].is_running)

    def test_one_hundred_fast_switch_presses_end_stopped(self):
        started = []
        stopped = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register(
            "mouse_back", started.append, TriggerMode.SWITCH, stopped.append,
            binding_id="macro",
        )
        for _ in range(100):
            manager._dispatch_physical_event("mouse_back", True)
            manager._dispatch_physical_event("mouse_back", False)
        self.assertEqual(len(started), 50)
        self.assertEqual(len(stopped), 50)
        self.assertFalse(manager._bindings_by_id["macro"].is_running)

    def test_key_autorepeat_is_deduplicated_before_entering_the_queue(self):
        manager = HotkeyManager()
        manager._listening = True
        for _ in range(100):
            manager._queue_physical_event("a", True)
        manager._queue_physical_event("a", False)
        self.assertEqual(manager._event_queue.qsize(), 2)
        manager.clear_pending_events()

    def test_physical_observer_receives_edge_before_macro_queue(self):
        manager = HotkeyManager()
        observed = []
        manager.add_physical_observer(observed.append)
        manager._on_windows_keyboard_event(
            0x0100, SimpleNamespace(vkCode=69, dwExtraInfo=0)
        )
        self.assertEqual(len(observed), 1)
        self.assertIsInstance(observed[0], PhysicalInputEvent)
        self.assertEqual((observed[0].hotkey, observed[0].pressed, observed[0].vk), ("e", True, 69))

    def test_physical_observer_never_receives_mapl_input(self):
        manager = HotkeyManager()
        observed = []
        manager.add_physical_observer(observed.append)
        manager._on_windows_keyboard_event(
            0x0100, SimpleNamespace(vkCode=69, dwExtraInfo=INPUT_EVENT_MARKER)
        )
        self.assertEqual(observed, [])

if __name__ == "__main__":
    unittest.main()
