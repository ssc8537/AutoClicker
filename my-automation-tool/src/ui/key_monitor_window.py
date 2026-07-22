"""显示时不抢焦点、主动点击详情后可浏览的全局物理按键浮窗。"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
import json
import math
import os
from pathlib import Path
import tempfile
import time

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.hotkey_manager import PhysicalInputEvent
from src.core.input_keys import normalise_input_key, physical_event_text, physical_input_name
from src.utils.app_paths import config_root


DEFAULT_MONITOR_KEYS = (
    "1", "2", "3", "q", "e", "r", "space",
    "mouse_left", "mouse_right", "mouse_back", "mouse_forward",
)
KEYBOARD_LAYOUT = (
    ("1", "2", "3"),
    ("q", "e", "r"),
    ("space",),
)
MOUSE_LAYOUT = (
    ("mouse_left", "mouse_right"),
    ("mouse_back", "mouse_forward"),
)
RECENT_COUNTS = (3, 5, 10)
PRESS_SEQUENCE_COLORS = (
    ("#F3A8BE", "#402234"),  # 樱花粉
    ("#F6C28B", "#4B2E18"),  # 淡桃橙
    ("#9DDEC1", "#183B2C"),  # 薄荷绿
    ("#85D8FF", "#17384A"),  # 天空蓝
    ("#C4B5F3", "#302554"),  # 薰衣草
)
PRESS_SEQUENCE_COLORS_ON_LIGHT = (
    "#9C3F63", "#9A5419", "#247A58", "#20719E", "#644CA5",
)
DETAIL_BACKGROUND_PRESETS = {
    "soft_black": ("淡黑色", (24, 30, 43)),
    "soft_white": ("淡白色", (244, 247, 252)),
    "cherry_pink": ("淡樱粉", (243, 168, 190)),
    "sky_blue": ("天空蓝", (133, 216, 255)),
    "mint_green": ("薄荷绿", (157, 222, 193)),
}


@dataclass(frozen=True)
class RecentInputEvent:
    text: str
    detail: str
    color_index: int


class CornerResizeHandle(QLabel):
    """只在一个可见角落内生效的精确缩放手柄。"""

    def __init__(self, corner: str, parent: QWidget):
        icons = {"top_left": "↖", "top_right": "↗", "bottom_left": "↙", "bottom_right": "↘"}
        super().__init__(icons[corner], parent)
        self.corner = corner
        self._press_global: QPoint | None = None
        self._start_geometry: QRect | None = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diagonal = Qt.CursorShape.SizeFDiagCursor if corner in {"top_left", "bottom_right"} else Qt.CursorShape.SizeBDiagCursor
        self.setCursor(diagonal)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_global = event.globalPosition().toPoint()
            self._start_geometry = self.window().geometry()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._press_global is None or self._start_geometry is None:
            super().mouseMoveEvent(event)
            return
        if not event.buttons() & Qt.MouseButton.LeftButton:
            return
        window = self.window()
        delta = event.globalPosition().toPoint() - self._press_global
        start = self._start_geometry
        min_w, min_h = window.minimumWidth(), window.minimumHeight()
        max_w, max_h = window.maximumWidth(), window.maximumHeight()
        left, top, right, bottom = start.left(), start.top(), start.right(), start.bottom()
        if "left" in self.corner:
            left = max(right - max_w + 1, min(right - min_w + 1, start.left() + delta.x()))
        else:
            right = min(left + max_w - 1, max(left + min_w - 1, start.right() + delta.x()))
        if "top" in self.corner:
            top = max(bottom - max_h + 1, min(bottom - min_h + 1, start.top() + delta.y()))
        else:
            bottom = min(top + max_h - 1, max(top + min_h - 1, start.bottom() + delta.y()))
        window.setGeometry(QRect(QPoint(left, top), QPoint(right, bottom)))
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._press_global = None
        self._start_geometry = None
        event.accept()


class EventHistoryScrollArea(QScrollArea):
    """透明事件列表；上下键每次精确移动一个可读单位。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("key_monitor_event_scroll")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollBar:vertical{background:rgba(255,255,255,24);width:7px;margin:0;}"
            "QScrollBar::handle:vertical{background:rgba(255,255,255,125);"
            "border-radius:3px;min-height:16px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:transparent;}"
        )

    def set_unit_step(self, pixels: int) -> None:
        self.verticalScrollBar().setSingleStep(max(1, int(pixels)))

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            bar = self.verticalScrollBar()
            direction = -1 if event.key() == Qt.Key.Key_Up else 1
            bar.setValue(bar.value() + direction * bar.singleStep())
            event.accept()
            return
        super().keyPressEvent(event)

class KeyMonitorWindow(QWidget):
    """透明白框按键窗；hook线程只发Signal，所有UI更新都在Qt线程。"""

    closed = Signal()
    physical_event_received = Signal(object)

    _MAX_KEYS = 32
    _BASE_TILE_WIDTH = 66
    _BASE_TILE_HEIGHT = 42
    _BASE_GAP = 7

    def __init__(self, parent=None, *, settings_path: Path | None = None):
        super().__init__(None)
        self._settings_path = settings_path or (config_root() / "key_monitor.json")
        (
            self._keys,
            self._recent_count,
            stored_size,
            self._stored_position,
            self._detail_background,
            self._detail_opacity,
            self._window_opacity,
        ) = self._load_settings()
        self._buttons: dict[str, QLabel] = {}
        self._pressed_at: dict[str, int] = {}
        self._press_colors: dict[str, int] = {}
        self._released_at: dict[str, int] = {}
        self._last_key: str | None = None
        self._last_event_ns: int | None = None
        self._press_sequence = 0
        self._wall_origin_ns = time.time_ns()
        self._mono_origin_ns = time.perf_counter_ns()
        self._recent_events: deque[RecentInputEvent] = deque(maxlen=10)
        self._recent_labels: list[QLabel] = []
        self._drag_offset: QPoint | None = None
        self._base_size = QSize(560, 340)
        self._position_restored = False
        self._setup_window()
        self._build_ui()
        self._recalculate_base_size(initial=True)
        if stored_size is not None:
            self.resize(
                max(self.minimumWidth(), stored_size.width()),
                max(self.minimumHeight(), stored_size.height()),
            )
        self._apply_scale()
        self.physical_event_received.connect(self._apply_physical_event)
        self._duration_timer = QTimer(self)
        self._duration_timer.setInterval(33)
        self._duration_timer.timeout.connect(self._refresh_live_duration)
        self._duration_timer.start()

    @property
    def keys(self) -> tuple[str, ...]:
        return self._keys

    @property
    def extra_keys(self) -> tuple[str, ...]:
        return tuple(key for key in self._keys if key not in DEFAULT_MONITOR_KEYS)

    @property
    def recent_count(self) -> int:
        return self._recent_count

    @property
    def detail_background(self) -> str:
        return self._detail_background

    @property
    def detail_opacity(self) -> int:
        return self._detail_opacity

    @property
    def window_opacity(self) -> int:
        return self._window_opacity

    def _setup_window(self) -> None:
        self.setWindowTitle("按键记录窗口")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def _build_ui(self) -> None:
        self._surface = QWidget(self)
        self._surface.setObjectName("key_monitor_surface")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        outer.addWidget(self._surface)
        self._layout = QVBoxLayout(self._surface)
        self._layout.setContentsMargins(12, 9, 12, 11)
        self._layout.setSpacing(8)

        header = QHBoxLayout()
        header.addSpacing(10)
        self._title = QLabel("按键记录")
        self._title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        header.addWidget(self._title)
        header.addStretch(1)
        self._clock_label = QLabel(self._current_local_time())
        self._clock_label.setObjectName("key_monitor_local_clock")
        self._clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clock_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        header.addWidget(self._clock_label)
        self._window_controls = QWidget()
        controls = QHBoxLayout(self._window_controls)
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(4)
        self._minimize_button = QPushButton("—")
        self._maximize_button = QPushButton("□")
        self._close_button = QPushButton("×")
        for button in (self._minimize_button, self._maximize_button, self._close_button):
            controls.addWidget(button)
        self._window_controls.hide()
        header.addWidget(self._window_controls)
        header.addSpacing(10)
        self._layout.addLayout(header)

        self._key_strip = QHBoxLayout()
        self._key_strip.setContentsMargins(0, 0, 0, 0)
        self._key_strip.setSpacing(12)
        self._keyboard_widget = QWidget()
        self._keyboard_grid = QGridLayout(self._keyboard_widget)
        self._keyboard_grid.setContentsMargins(0, 0, 0, 0)
        self._mouse_widget = QWidget()
        self._mouse_grid = QGridLayout(self._mouse_widget)
        self._mouse_grid.setContentsMargins(0, 0, 0, 0)
        self._extra_widget = QWidget()
        self._extra_grid = QGridLayout(self._extra_widget)
        self._extra_grid.setContentsMargins(0, 0, 0, 0)
        self._key_strip.addWidget(self._keyboard_widget)
        self._key_strip.addWidget(self._mouse_widget)
        self._key_strip.addWidget(self._extra_widget)
        self._key_strip.addStretch(1)
        self._layout.addLayout(self._key_strip)

        self._details_panel = QWidget()
        self._details_panel.setObjectName("key_monitor_details_panel")
        details_layout = QVBoxLayout(self._details_panel)
        details_layout.setContentsMargins(7, 6, 7, 6)
        details_layout.setSpacing(4)

        detail_header = QHBoxLayout()
        self._history_title = QLabel()
        self._history_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        detail_header.addWidget(self._history_title)
        detail_header.addStretch(1)
        details_layout.addLayout(detail_header)

        self._history_scroll = EventHistoryScrollArea()
        self._history_content = QWidget()
        self._history_content.setStyleSheet("background:transparent;")
        self._history_layout = QVBoxLayout(self._history_content)
        self._history_layout.setContentsMargins(0, 0, 0, 0)
        self._history_layout.setSpacing(3)
        self._history_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        for _index in range(10):
            label = QLabel("等待物理按键")
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
            )
            self._recent_labels.append(label)
            self._history_layout.addWidget(label)
        self._last_event = self._recent_labels[0]
        self._history_scroll.setWidget(self._history_content)
        details_layout.addWidget(self._history_scroll, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(6)
        self._hold_detail = QLabel("按住：—")
        self._release_detail = QLabel("松开：—")
        self._hold_detail.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._release_detail.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        footer.addWidget(self._hold_detail)
        footer.addWidget(self._release_detail)
        self._scratch_input = QLineEdit()
        self._scratch_input.setObjectName("key_monitor_scratch_input")
        self._scratch_input.setPlaceholderText("可以在此输入按键")
        self._scratch_input.setMaxLength(1_000_000)
        self._scratch_input.setClearButtonEnabled(False)
        self._scratch_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._scratch_input.setAccessibleName("临时按键输入框")
        self._scratch_input.setToolTip("仅临时保留；关闭按键记录窗口后自动清空")
        placeholder_palette = self._scratch_input.palette()
        placeholder_palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(168, 172, 182, 210)
        )
        self._scratch_input.setPalette(placeholder_palette)
        footer.addWidget(self._scratch_input, 1)
        details_layout.addLayout(footer)
        self._layout.addWidget(self._details_panel)

        self._resize_handles = {
            corner: CornerResizeHandle(corner, self)
            for corner in ("top_left", "top_right", "bottom_left", "bottom_right")
        }
        for handle in self._resize_handles.values():
            handle.hide()

        self._minimize_button.clicked.connect(self.showMinimized)
        self._maximize_button.clicked.connect(self._toggle_maximized)
        self._close_button.clicked.connect(self.close)
        self._rebuild_key_grid()
        self._render_recent_events()

    def set_keys(self, keys, *, persist: bool = True) -> None:
        """保存完整可见键集合；默认键首次勾选，但允许用户取消。"""
        normalized: list[str] = []
        for value in keys:
            try:
                key = normalise_input_key(value)
            except ValueError:
                continue
            if key not in normalized:
                normalized.append(key)
        self._keys = tuple(normalized[: self._MAX_KEYS])
        if persist:
            self._save_settings()
        self._rebuild_key_grid()
        self._recalculate_base_size()

    def set_extra_keys(self, keys) -> None:
        """旧接口兼容：在当前选中的默认键之后设置额外键。"""
        selected_defaults = [key for key in DEFAULT_MONITOR_KEYS if key in self._keys]
        self.set_keys((*selected_defaults, *keys))

    def set_recent_count(self, count: int, *, persist: bool = True) -> None:
        self._recent_count = count if count in RECENT_COUNTS else 3
        if persist:
            self._save_settings()
        self._render_recent_events()
        self._recalculate_base_size()

    def set_appearance(
        self,
        detail_background: str,
        detail_opacity: int,
        window_opacity: int,
        *,
        persist: bool = True,
    ) -> None:
        self._detail_background = (
            detail_background
            if detail_background in DETAIL_BACKGROUND_PRESETS
            else "soft_black"
        )
        self._detail_opacity = max(0, min(100, int(detail_opacity)))
        self._window_opacity = max(0, min(100, int(window_opacity)))
        if persist:
            self._save_settings()
        self._apply_scale()

    def save_settings(self) -> None:
        """提交已经实时预览过的当前设置。"""
        self._save_settings()

    def _clear_grid(self, grid: QGridLayout) -> None:
        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

    def _make_tile(self, key: str) -> QLabel:
        tile = QLabel(physical_input_name(key).replace("大写 ", ""))
        tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tile.setTextFormat(Qt.TextFormat.PlainText)
        tile.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        tile.setObjectName("key_state_" + key.replace(" ", "_").replace("mouse_", "mouse_"))
        self._buttons[key] = tile
        return tile

    def _rebuild_key_grid(self) -> None:
        for grid in (self._keyboard_grid, self._mouse_grid, self._extra_grid):
            self._clear_grid(grid)
            grid.setHorizontalSpacing(self._BASE_GAP)
            grid.setVerticalSpacing(self._BASE_GAP)
        self._buttons.clear()
        selected = set(self._keys)

        for row, keys in enumerate(KEYBOARD_LAYOUT):
            if keys == ("space",):
                if "space" in selected:
                    self._keyboard_grid.addWidget(self._make_tile("space"), row, 0, 1, 3)
            else:
                for column, key in enumerate(keys):
                    if key in selected:
                        self._keyboard_grid.addWidget(self._make_tile(key), row, column)

        for row, keys in enumerate(MOUSE_LAYOUT):
            for column, key in enumerate(keys):
                if key in selected:
                    self._mouse_grid.addWidget(self._make_tile(key), row, column)

        extras = self.extra_keys
        for index, key in enumerate(extras):
            self._extra_grid.addWidget(self._make_tile(key), index // 4, index % 4)
        keyboard_keys = {key for row in KEYBOARD_LAYOUT for key in row}
        mouse_keys = {key for row in MOUSE_LAYOUT for key in row}
        self._keyboard_widget.setVisible(bool(selected & keyboard_keys))
        self._mouse_widget.setVisible(bool(selected & mouse_keys))
        self._extra_widget.setVisible(bool(extras))
        for key in self._buttons:
            self._style_button(key, key in self._pressed_at)
        self._apply_scale()

    def observe_input(self, event: PhysicalInputEvent) -> None:
        self.physical_event_received.emit(event)

    @Slot(object)
    def _apply_physical_event(self, event: PhysicalInputEvent) -> None:
        key = event.hotkey
        if key not in self._buttons:
            return
        now = event.monotonic_ns
        if event.pressed and key in self._pressed_at:
            return
        if not event.pressed and key not in self._pressed_at:
            return
        self._last_key = key
        delta_ms = (
            None
            if self._last_event_ns is None
            else (now - self._last_event_ns) / 1_000_000
        )
        self._last_event_ns = now
        if event.pressed:
            previous_release = self._released_at.get(key)
            release_ms = None if previous_release is None else (now - previous_release) / 1_000_000
            self._pressed_at[key] = now
            color_index = self._press_sequence % len(PRESS_SEQUENCE_COLORS)
            self._press_sequence += 1
            self._press_colors[key] = color_index
            self._hold_detail.setText("按下：0.0 ms")
            self._release_detail.setText(
                "松开：—" if release_ms is None else f"松开：{release_ms:.1f} ms"
            )
            parts = [
                "首次按下"
                if release_ms is None
                else f"松开间隔 {release_ms:.1f} ms"
            ]
            if delta_ms is not None:
                parts.append(f"距上一事件 +{delta_ms:.1f} ms")
            overlaps = [
                physical_input_name(active_key)
                for active_key in self._pressed_at
                if active_key != key
            ]
            if overlaps:
                parts.append("同时按住：" + " / ".join(overlaps))
            detail = " · ".join(parts)
            self._append_recent_event(key, True, detail, color_index, now)
            self._style_button(key, True)
            return

        previous_press = self._pressed_at.pop(key, None)
        color_index = self._press_colors.pop(key, (self._press_sequence - 1) % len(PRESS_SEQUENCE_COLORS))
        hold_ms = (now - previous_press) / 1_000_000
        self._hold_detail.setText(f"按下：{hold_ms:.1f} ms")
        self._release_detail.setText("松开：0.0 ms")
        self._released_at[key] = now
        parts = [f"按下时长 {hold_ms:.1f} ms"]
        if delta_ms is not None:
            parts.append(f"距上一事件 +{delta_ms:.1f} ms")
        remaining = [physical_input_name(active_key) for active_key in self._pressed_at]
        if remaining:
            parts.append("仍在按住：" + " / ".join(remaining))
        self._append_recent_event(
            key, False, " · ".join(parts), color_index, now
        )
        self._style_button(key, False)

    def _append_recent_event(
        self,
        key: str,
        pressed: bool,
        detail: str,
        color_index: int,
        monotonic_ns: int,
    ) -> None:
        timestamp = self._local_time_for_monotonic(monotonic_ns)
        self._recent_events.append(
            RecentInputEvent(
                f"{timestamp}  {'按下' if pressed else '松开'} {physical_input_name(key)}",
                detail,
                color_index,
            )
        )
        self._render_recent_events()

    def _render_recent_events(self) -> None:
        self._history_title.setText(f"最近 {self._recent_count} 个事件")
        # 时间线自上而下阅读：保留范围内最旧的在上，最新的在下。
        events = list(self._recent_events)[-self._recent_count :]
        scale = self._current_scale()
        radius = max(3, round(6 * scale))
        vertical_padding = max(2, round(3 * scale))
        horizontal_padding = max(4, round(7 * scale))
        for index, label in enumerate(self._recent_labels):
            visible = index < self._recent_count
            label.setVisible(visible)
            if not visible:
                continue
            if index < len(events):
                item = events[index]
                label.setText(f"{item.text}  ·  {item.detail}")
                event_color = self._event_text_color(item.color_index)
                label.setStyleSheet(
                    f"color: {event_color}; background-color: {self._detail_rgba(min(100, self._detail_opacity + 12))}; "
                    f"border: 1px solid rgba(255,255,255,85); border-radius: {radius}px; "
                    f"font-size: {max(7, round(11 * scale))}px; "
                    f"padding: {vertical_padding}px {horizontal_padding}px;"
                )
            else:
                label.setText("等待物理按键")
                label.setStyleSheet(
                    f"color: {self._neutral_detail_text()}; background-color: {self._detail_rgba(min(100, self._detail_opacity + 8))}; "
                    f"border: 1px solid rgba(255,255,255,70); border-radius: {radius}px; "
                    f"font-size: {max(7, round(11 * scale))}px; "
                    f"padding: {vertical_padding}px {horizontal_padding}px;"
                )
            label.updateGeometry()
        if events:
            self._last_event = self._recent_labels[len(events) - 1]
        else:
            self._last_event = self._recent_labels[0]
        self._history_content.updateGeometry()
        self._history_scroll.set_unit_step(max(12, round(24 * scale)))

    def _refresh_live_duration(self) -> None:
        self._clock_label.setText(self._current_local_time())
        key = self._last_key
        if key is None:
            return
        now = time.perf_counter_ns()
        if key in self._pressed_at:
            elapsed = (now - self._pressed_at[key]) / 1_000_000
            self._hold_detail.setText(f"按下：{elapsed:.1f} ms")
        elif key in self._released_at:
            elapsed = (now - self._released_at[key]) / 1_000_000
            self._release_detail.setText(f"松开：{elapsed:.1f} ms")

    @staticmethod
    def _current_local_time() -> str:
        return datetime.now().strftime("%H:%M:%S:%f")[:-3]

    def _local_time_for_monotonic(self, monotonic_ns: int) -> str:
        wall_ns = self._wall_origin_ns + monotonic_ns - self._mono_origin_ns
        return datetime.fromtimestamp(wall_ns / 1_000_000_000).strftime("%H:%M:%S:%f")[:-3]

    def _detail_rgb(self) -> tuple[int, int, int]:
        return DETAIL_BACKGROUND_PRESETS[self._detail_background][1]

    def _detail_rgba(self, opacity: int | None = None) -> str:
        red, green, blue = self._detail_rgb()
        percent = self._detail_opacity if opacity is None else opacity
        alpha = round(255 * max(0, min(100, percent)) / 100)
        return f"rgba({red},{green},{blue},{alpha})"

    def _detail_is_light(self) -> bool:
        red, green, blue = self._detail_rgb()
        return (red * 299 + green * 587 + blue * 114) / 1000 > 170

    def _event_text_color(self, color_index: int) -> str:
        if self._detail_is_light():
            return PRESS_SEQUENCE_COLORS_ON_LIGHT[color_index % len(PRESS_SEQUENCE_COLORS_ON_LIGHT)]
        return PRESS_SEQUENCE_COLORS[color_index % len(PRESS_SEQUENCE_COLORS)][0]

    def _neutral_detail_text(self) -> str:
        return "rgba(44,48,61,210)" if self._detail_is_light() else "rgba(255,255,255,180)"

    def _style_button(self, key: str, pressed: bool) -> None:
        tile = self._buttons.get(key)
        if tile is None:
            return
        scale = self._current_scale()
        radius = max(3, round(7 * scale))
        font_size = max(7, round(13 * scale))
        if pressed:
            color_index = self._press_colors.get(key, 0)
            background, text_color = PRESS_SEQUENCE_COLORS[color_index]
            tile.setStyleSheet(
                f"QLabel {{ background: {background}; color: {text_color}; "
                f"border: 2px solid rgba(255,255,255,245); border-radius: {radius}px; "
                f"font-size: {font_size}px; font-weight: 800; }}"
            )
        else:
            tile.setStyleSheet(
                f"QLabel {{ background: rgba(0,0,0,28); color: rgba(255,255,255,245); "
                f"border: 2px solid rgba(255,255,255,225); border-radius: {radius}px; "
                f"font-size: {font_size}px; font-weight: 750; }}"
            )

    def _current_scale(self) -> float:
        if self._base_size.width() <= 0 or self._base_size.height() <= 0:
            return 1.0
        return max(
            0.5,
            min(1.5, min(self.width() / self._base_size.width(), self.height() / self._base_size.height())),
        )

    def _recalculate_base_size(self, *, initial: bool = False) -> None:
        old_base = self._base_size
        old_scale = 1.0 if initial else self._current_scale()
        selected = set(self._keys)
        keyboard_keys = {key for row in KEYBOARD_LAYOUT for key in row}
        mouse_keys = {key for row in MOUSE_LAYOUT for key in row}
        extras = self.extra_keys
        extra_columns = min(4, len(extras))
        extra_rows = math.ceil(len(extras) / 4) if extras else 0
        width = 80
        if selected & keyboard_keys:
            width += 212
        if selected & mouse_keys:
            width += 146
        if extra_columns:
            width += extra_columns * (self._BASE_TILE_WIDTH + self._BASE_GAP)
        keyboard_rows = max(
            (row + 1 for row, keys in enumerate(KEYBOARD_LAYOUT) if selected.intersection(keys)),
            default=0,
        )
        mouse_rows = max(
            (row + 1 for row, keys in enumerate(MOUSE_LAYOUT) if selected.intersection(keys)),
            default=0,
        )
        key_rows = max(1, keyboard_rows, mouse_rows, extra_rows)
        height = 130 + key_rows * (self._BASE_TILE_HEIGHT + self._BASE_GAP) + self._recent_count * 28
        self._base_size = QSize(min(850, max(280, width)), min(650, height))
        self.setMinimumSize(
            max(210, self._base_size.width() // 2),
            max(170, self._base_size.height() // 2),
        )
        self.setMaximumSize(self._base_size.width() * 2, self._base_size.height() * 2)
        if initial:
            self.resize(self._base_size)
        elif old_base != self._base_size:
            self.resize(
                max(self.minimumWidth(), round(self._base_size.width() * old_scale)),
                max(self.minimumHeight(), round(self._base_size.height() * old_scale)),
            )
        self._apply_scale()

    def _apply_scale(self) -> None:
        if not hasattr(self, "_layout"):
            return
        scale = self._current_scale()
        margin_x = max(6, round(12 * scale))
        margin_y = max(5, round(9 * scale))
        gap = max(3, round(self._BASE_GAP * scale))
        self._layout.setContentsMargins(margin_x, margin_y, margin_x, margin_y)
        self._layout.setSpacing(max(4, round(8 * scale)))
        self._key_strip.setSpacing(max(6, round(12 * scale)))
        for grid in (self._keyboard_grid, self._mouse_grid, self._extra_grid):
            grid.setHorizontalSpacing(gap)
            grid.setVerticalSpacing(gap)
        tile_width = max(32, round(self._BASE_TILE_WIDTH * scale))
        tile_height = max(21, round(self._BASE_TILE_HEIGHT * scale))
        for key, tile in self._buttons.items():
            width = tile_width * 3 + gap * 2 if key == "space" else tile_width
            tile.setFixedSize(width, tile_height)
            self._style_button(key, key in self._pressed_at)
        title_px = max(8, round(16 * scale))
        body_px = max(7, round(11 * scale))
        self._title.setStyleSheet(
            f"color: rgba(255,255,255,245); font-size: {title_px}px; font-weight: 800; background: transparent;"
        )
        self._history_title.setStyleSheet(
            f"color: {self._neutral_detail_text()}; font-size: {body_px}px; font-weight: 800; background: transparent;"
        )
        self._clock_label.setStyleSheet(
            f"color: rgba(255,255,255,245); background: rgba(0,0,0,32); "
            f"border: 1px solid rgba(255,255,255,205); border-radius: {max(4, round(7 * scale))}px; "
            f"padding: {max(2, round(3 * scale))}px {max(4, round(7 * scale))}px; "
            f"font-size: {body_px}px; font-weight: 800;"
        )
        for label in (*self._recent_labels, self._hold_detail, self._release_detail):
            font = label.font()
            font.setPixelSize(body_px)
            label.setFont(font)
        detail_text = self._neutral_detail_text()
        self._hold_detail.setStyleSheet(f"color: {detail_text}; background: transparent;")
        self._release_detail.setStyleSheet(f"color: {detail_text}; background: transparent;")
        scratch_height = max(22, round(30 * scale))
        self._scratch_input.setFixedHeight(scratch_height)
        self._scratch_input.setMinimumWidth(max(90, round(190 * scale)))
        self._scratch_input.setStyleSheet(
            f"QLineEdit#key_monitor_scratch_input {{ color: {detail_text}; "
            "background-color: rgba(255,255,255,24); "
            "border: 1px solid rgba(255,255,255,125); "
            f"border-radius: {max(4, round(7 * scale))}px; "
            f"padding: 0 {max(5, round(8 * scale))}px; font-size: {body_px}px; }} "
            "QLineEdit#key_monitor_scratch_input:focus { "
            "border-color: rgba(243,168,190,220); background-color: rgba(255,255,255,38); }"
        )
        self._details_panel.setStyleSheet(
            f"QWidget#key_monitor_details_panel {{ background-color: {self._detail_rgba()}; "
            f"border: 1px solid rgba(255,255,255,90); border-radius: {max(5, round(9 * scale))}px; }}"
        )
        control_size = max(18, round(25 * scale))
        for button in (self._minimize_button, self._maximize_button, self._close_button):
            button.setFixedSize(control_size, control_size)
            button.setStyleSheet(
                f"QPushButton {{ color: white; background: rgba(0,0,0,65); border: 1px solid rgba(255,255,255,150); "
                f"border-radius: {max(4, control_size // 2)}px; font-size: {max(8, round(12 * scale))}px; }}"
                "QPushButton:hover { background: rgba(243,168,190,180); }"
            )
        window_alpha = round(255 * self._window_opacity / 100)
        self._surface.setStyleSheet(
            f"QWidget#key_monitor_surface {{ background: rgba(5,8,13,{window_alpha}); "
            f"border: 1px solid rgba(255,255,255,100); border-radius: {max(7, round(14 * scale))}px; }}"
        )
        handle_size = max(8, round(10 * scale))
        for handle in self._resize_handles.values():
            handle.setFixedSize(handle_size, handle_size)
            handle.setStyleSheet(
                f"color: white; background: rgba(16,20,30,205); border: 1px solid rgba(255,255,255,220); "
                f"border-radius: {max(2, round(3 * scale))}px; font-size: {max(7, round(8 * scale))}px; font-weight: 900;"
            )
        self._position_resize_handles()
        self._render_recent_events()

    def _position_resize_handles(self) -> None:
        if not hasattr(self, "_resize_handles"):
            return
        inset = 2
        width, height = self.width(), self.height()
        for corner, handle in self._resize_handles.items():
            x = inset if "left" in corner else width - handle.width() - inset
            y = inset if "top" in corner else height - handle.height() - inset
            handle.move(x, y)
            handle.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_scale()

    def _toggle_maximized(self) -> None:
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def enterEvent(self, event) -> None:
        self._window_controls.show()
        for handle in self._resize_handles.values():
            handle.show()
            handle.raise_()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._window_controls.hide()
        for handle in self._resize_handles.values():
            handle.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._position_restored:
            return
        self._position_restored = True
        screens = QApplication.screens()
        if not screens:
            return
        target = self._stored_position
        screen = QApplication.screenAt(target) if target is not None else None
        screen = screen or QApplication.primaryScreen() or screens[0]
        area = screen.availableGeometry()
        if target is None:
            target = QPoint(area.right() - self.width() - 23, area.top() + 24)
        right_limit = max(area.left(), area.right() - self.width() + 1)
        bottom_limit = max(area.top(), area.bottom() - self.height() + 1)
        self.move(
            max(area.left(), min(target.x(), right_limit)),
            max(area.top(), min(target.y(), bottom_limit)),
        )

    def closeEvent(self, event) -> None:
        # 这是一次性草稿区：关闭浮窗时先清空，且绝不写入设置或录像文件。
        self._scratch_input.clear()
        self._save_settings()
        self.closed.emit()
        super().closeEvent(event)

    def _load_settings(
        self,
    ) -> tuple[tuple[str, ...], int, QSize | None, QPoint | None, str, int, int]:
        try:
            data = json.loads(self._settings_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError):
            return DEFAULT_MONITOR_KEYS, 3, None, None, "soft_black", 58, 28

        schema = data.get("schema", 1)
        if schema >= 3 and isinstance(data.get("keys"), list):
            raw_keys = data["keys"]
        elif schema == 2:
            raw_extra = data.get("extra_keys", [])
            raw_keys = [*DEFAULT_MONITOR_KEYS, *(raw_extra if isinstance(raw_extra, list) else [])]
        elif isinstance(data.get("keys"), list):
            raw_keys = data["keys"]
        else:
            raw_keys = list(DEFAULT_MONITOR_KEYS)
        selected: list[str] = []
        if isinstance(raw_keys, list):
            for value in raw_keys:
                try:
                    key = normalise_input_key(value)
                except (ValueError, TypeError):
                    continue
                if key not in selected:
                    selected.append(key)
        recent_count = data.get("recent_count", 3)
        if recent_count not in RECENT_COUNTS:
            recent_count = 3
        width = data.get("window_width")
        height = data.get("window_height")
        stored_size = None
        if isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
            stored_size = QSize(width, height)
        position_x = data.get("window_x")
        position_y = data.get("window_y")
        stored_position = None
        if isinstance(position_x, int) and isinstance(position_y, int):
            stored_position = QPoint(position_x, position_y)
        detail_background = data.get("detail_background", "soft_black")
        if detail_background not in DETAIL_BACKGROUND_PRESETS:
            detail_background = "soft_black"
        detail_opacity = data.get("detail_opacity", 58)
        if not isinstance(detail_opacity, int):
            detail_opacity = 58
        window_opacity = data.get("window_opacity", 28)
        if not isinstance(window_opacity, int):
            window_opacity = 28
        return (
            tuple(selected[: self._MAX_KEYS]),
            recent_count,
            stored_size,
            stored_position,
            detail_background,
            max(0, min(100, detail_opacity)),
            max(0, min(100, window_opacity)),
        )

    def _save_settings(self) -> None:
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self._settings_path.name}.",
                dir=self._settings_path.parent,
                text=True,
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(
                    {
                        "schema": 5,
                        "keys": list(self._keys),
                        "recent_count": self._recent_count,
                        "detail_background": self._detail_background,
                        "detail_opacity": self._detail_opacity,
                        "window_opacity": self._window_opacity,
                        "window_width": self.width(),
                        "window_height": self.height(),
                        "window_x": self.x(),
                        "window_y": self.y(),
                    },
                    stream,
                    ensure_ascii=False,
                    indent=2,
                )
                stream.write("\n")
            os.replace(temporary_name, self._settings_path)
        finally:
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)
