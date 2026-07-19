"""触发详情用的自绘上下箭头数字框。"""
from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPolygon
from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox, QStyle, QStyleOptionSpinBox


def _draw_rose_arrows(widget) -> None:
    """在 Qt 按钮背景上叠加高对比酒红三角，避免系统主题隐藏箭头。"""
    option = QStyleOptionSpinBox()
    widget.initStyleOption(option)
    painter = QPainter(widget)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#6E4055") if widget.isEnabled() else QColor("#B7A7AF"))
        triangles = (
            (QStyle.SubControl.SC_SpinBoxUp, (QPoint(-4, 2), QPoint(4, 2), QPoint(0, -3))),
            (QStyle.SubControl.SC_SpinBoxDown, (QPoint(-4, -2), QPoint(4, -2), QPoint(0, 3))),
        )
        for control, offsets in triangles:
            rect = widget.style().subControlRect(
                QStyle.ComplexControl.CC_SpinBox, option, control, widget
            )
            if not rect.isEmpty():
                center = rect.center()
                painter.drawPolygon(QPolygon([center + offset for offset in offsets]))
    finally:
        painter.end()


class RoseSpinBox(QSpinBox):
    """带稳定可见箭头的整数数字框。"""

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt callback name
        super().paintEvent(event)
        _draw_rose_arrows(self)


class RoseDoubleSpinBox(QDoubleSpinBox):
    """带稳定可见箭头的小数数字框。"""

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt callback name
        super().paintEvent(event)
        _draw_rose_arrows(self)
