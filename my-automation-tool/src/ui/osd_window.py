"""OSD浮层窗口 — 在屏幕顶部居中显示提示文本。

参考 Quickinput PopsUi.cpp 的全局 Overlay 窗口设计。
用 PySide6 创建无边框、透明背景、置顶浮层。
"""
import json
import os
import tempfile
from pathlib import Path

from src.utils.app_paths import config_root

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QColor, QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QApplication, QGraphicsDropShadowEffect, QSizePolicy,
)


class OsdPopup(QWidget):
    """屏幕提示文本浮层窗口，脚本执行/结束时在屏幕顶部居中显示提示。"""

    _SETTINGS_PATH = config_root() / "settings.json"
    _MIN_WIDTH = 320
    _MIN_HEIGHT = 60
    _HORIZONTAL_MARGIN = 24
    _VERTICAL_MARGIN = 10
    _SHADOW_GUARD = 20
    _SCREEN_MARGIN = 24

    def __init__(self, parent=None, *, settings_path: Path | None = None):
        # OSD 是全局工具浮层，不能依附主窗口，否则会随主窗口层级和生命周期变化。
        super().__init__(None)
        self._settings_path = settings_path or self._SETTINGS_PATH
        self._setup_window_flags()
        self._load_config()
        self.resize(self._MIN_WIDTH, self._MIN_HEIGHT)
        self._setup_ui()
        self._setup_animation()

    def _setup_window_flags(self):
        """配置窗口标志：无边框 + 置顶 + 工具窗口（不在任务栏显示）。"""
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def _load_config(self):
        """从 settings.json 加载OSD配置，失败时用默认值。"""
        self.popup_enabled = True
        self.popup_y = 10
        self.popup_size = 24
        self.popup_duration_ms = 2000
        self.popup_success_color = "#00FF00"
        self.popup_end_color = "#FF0000"
        self.popup_background_enabled = False
        self._current_color = self.popup_success_color
        try:
            if self._settings_path.exists():
                with open(self._settings_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.popup_enabled = cfg.get("popup_enabled", True)
                self.popup_y = cfg.get("popup_position_y", 10)
                self.popup_size = cfg.get("popup_size", 24)
                self.popup_duration_ms = cfg.get("popup_duration_ms", 2000)
                self.popup_success_color = cfg.get("popup_success_color", "#00FF00")
                self.popup_end_color = cfg.get("popup_end_color", "#FF0000")
                self._current_color = self.popup_success_color
                self.popup_background_enabled = bool(
                    cfg.get("popup_background_enabled", False)
                )
        except Exception:
            pass

    def set_enabled(self, enabled: bool) -> None:
        """立即显示/隐藏 OSD 设置，并与其它 settings.json 字段和平共存。"""
        self.popup_enabled = bool(enabled)
        if not self.popup_enabled:
            self._hide_timer.stop()
            self._fade_anim.stop()
            self.hide()
        self._save_config_value("popup_enabled", self.popup_enabled)

    def set_size(self, size: int) -> None:
        """立即调整 OSD 字号并持久化。"""
        self.popup_size = max(10, min(72, int(size)))
        self._label.setFont(QFont("Microsoft YaHei", self.popup_size, QFont.Bold))
        if self._label.text():
            self._resize_for_text(self._label.text())
            self.update_position()
        self._save_config_value("popup_size", self.popup_size)

    def set_background_enabled(self, enabled: bool) -> None:
        """切换不遮挡游戏的半透明樱云背景。"""
        self.popup_background_enabled = bool(enabled)
        self._apply_label_style(self._current_color)
        self._save_config_value(
            "popup_background_enabled", self.popup_background_enabled
        )

    def _save_config_value(self, key: str, value) -> None:
        temporary_name = None
        try:
            data = {}
            if self._settings_path.is_file():
                loaded = json.loads(self._settings_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
            data[key] = value
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self._settings_path.name}.",
                dir=self._settings_path.parent,
                text=True,
            )
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as temporary:
                json.dump(data, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
            os.replace(temporary_name, self._settings_path)
        except (OSError, UnicodeError, json.JSONDecodeError):
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)

    def _setup_ui(self):
        """初始化标签和阴影效果。"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            self._HORIZONTAL_MARGIN,
            self._VERTICAL_MARGIN,
            self._HORIZONTAL_MARGIN,
            self._VERTICAL_MARGIN,
        )

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._label.setTextFormat(Qt.TextFormat.PlainText)
        self._label.setFont(QFont("Microsoft YaHei", self.popup_size, QFont.Bold))
        self._apply_label_style(self._current_color)
        layout.addWidget(self._label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 160))
        self._label.setGraphicsEffect(shadow)

    def _apply_label_style(self, color: str) -> None:
        background = (
            "rgba(255, 244, 249, 72)" if self.popup_background_enabled else "transparent"
        )
        border = "1px solid rgba(255, 255, 255, 120)" if self.popup_background_enabled else "none"
        radius = 12 if self.popup_background_enabled else 0
        self._label.setStyleSheet(
            f"color: {color}; background-color: {background}; "
            f"border: {border}; border-radius: {radius}px; padding: 3px 10px;"
        )

    def _setup_animation(self):
        """初始化淡出动画和自动隐藏定时器。"""
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(500)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.finished.connect(self.hide)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)

    def _resize_for_text(self, text: str) -> None:
        """按完整文字自适应 OSD；超过屏幕宽度时换行增高，不省略名称。"""
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            max_width = self._MIN_WIDTH
        else:
            max_width = max(
                self._MIN_WIDTH,
                screen.availableGeometry().width() - (self._SCREEN_MARGIN * 2),
            )

        metrics = QFontMetrics(self._label.font())
        single_line_width = (
            metrics.horizontalAdvance(text)
            + (self._HORIZONTAL_MARGIN * 2)
            + self._SHADOW_GUARD
        )
        target_width = min(max_width, max(self._MIN_WIDTH, single_line_width))

        should_wrap = single_line_width > max_width
        self._label.setWordWrap(should_wrap)
        label_horizontal_padding = 22
        label_vertical_padding = 8
        if should_wrap:
            label_width = max(
                1,
                target_width
                - (self._HORIZONTAL_MARGIN * 2)
                - self._SHADOW_GUARD,
            )
            wrap_width = max(1, label_width - label_horizontal_padding)
            bounds = metrics.boundingRect(
                QRect(0, 0, wrap_width, 10000),
                int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignHCenter),
                text,
            )
            content_height = bounds.height()
        else:
            label_width = metrics.horizontalAdvance(text) + label_horizontal_padding
            content_height = metrics.height()

        label_height = content_height + label_vertical_padding
        self._label.setFixedSize(label_width, label_height)

        target_height = max(
            self._MIN_HEIGHT,
            label_height + (self._VERTICAL_MARGIN * 2) + self._SHADOW_GUARD,
        )
        self.setFixedSize(target_width, target_height)

    def show_notification(self, text: str, success: bool = True):
        """显示提示文本，停留后自动淡出。

        Args:
            text: 要显示的文本
            success: True 用成功颜色（绿），False 用结束颜色（红）
        """
        if not self.popup_enabled:
            return

        # 更新文本和颜色
        self._label.setText(text)
        color = self.popup_success_color if success else self.popup_end_color
        self._current_color = color
        self._apply_label_style(color)

        # 先按实际字体计算完整文本尺寸，再重新居中，避免长脚本名左右被裁掉。
        self._resize_for_text(text)

        # 重置位置（响应屏幕分辨率变化）
        self.update_position()

        # 重置动画状态
        self._hide_timer.stop()
        self._fade_anim.stop()
        self.setWindowOpacity(1.0)

        # 显示并置顶
        self.show()
        self.raise_()

        # 启动自动隐藏计时
        self._hide_timer.start(self.popup_duration_ms)

    def _start_fade_out(self):
        """执行淡出动画。"""
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    def update_position(self):
        """移动到屏幕顶部居中位置。"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.left() + (geo.width() - self.width()) // 2
        y = geo.top() + self.popup_y
        self.move(x, y)
