"""纯 Python 绘制自有粉发头像，并导出窗口/托盘/EXE 共用 ICO。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "myautoplayer-pink.ico"


def _brush_gradient(start: QColor, end: QColor, y1: float, y2: float) -> QLinearGradient:
    gradient = QLinearGradient(128, y1, 128, y2)
    gradient.setColorAt(0, start)
    gradient.setColorAt(1, end)
    return gradient


def main() -> int:
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 高对比圆形底：小尺寸下仍先识别到酒红外轮廓与粉发。
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_brush_gradient(QColor("#FBE0E4"), QColor("#D58A9E"), 18, 238))
    painter.drawRoundedRect(QRectF(10, 10, 236, 236), 68, 68)
    painter.setPen(QPen(QColor("#E5A86B"), 8))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(18, 18, 220, 220), 58, 58)

    # 粉发大轮廓。
    hair = QPainterPath()
    hair.moveTo(56, 186)
    hair.cubicTo(37, 124, 58, 57, 128, 48)
    hair.cubicTo(203, 51, 223, 119, 202, 194)
    hair.cubicTo(184, 222, 77, 222, 56, 186)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_brush_gradient(QColor("#F8B4C8"), QColor("#B9597D"), 52, 218))
    painter.drawPath(hair)

    # 脸部与耳朵：简化五官，避免小图标变糊。
    painter.setBrush(QColor("#FFE7DE"))
    painter.drawEllipse(QRectF(82, 75, 96, 112))
    painter.drawEllipse(QRectF(73, 126, 22, 35))
    painter.drawEllipse(QRectF(161, 126, 22, 35))

    # 刘海和两侧卷发。
    painter.setBrush(QColor("#C96991"))
    fringe = QPainterPath()
    fringe.moveTo(76, 112)
    fringe.cubicTo(78, 61, 167, 52, 186, 108)
    fringe.cubicTo(167, 90, 149, 93, 136, 113)
    fringe.cubicTo(119, 88, 95, 97, 76, 112)
    painter.drawPath(fringe)
    painter.setPen(QPen(QColor("#A94D78"), 13, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawArc(QRectF(48, 92, 72, 122), 85 * 16, 170 * 16)
    painter.drawArc(QRectF(136, 92, 72, 122), -75 * 16, 170 * 16)

    # 大而清晰的眼睛、鼻口与玫瑰金耳饰。
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#6E4055"))
    painter.drawEllipse(QRectF(103, 127, 13, 17))
    painter.drawEllipse(QRectF(140, 127, 13, 17))
    painter.setPen(QPen(QColor("#B76284"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(121, 162), QPointF(136, 162))
    painter.setPen(QPen(QColor("#E29A52"), 5))
    painter.setBrush(QColor("#FFE5B5"))
    painter.drawEllipse(QRectF(166, 153, 15, 15))

    # 珍珠发卡：三个大点保持小尺寸可辨认。
    painter.setPen(QPen(QColor("#F0B36B"), 4))
    painter.drawLine(QPointF(148, 74), QPointF(183, 91))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#FFF9F4"))
    for x, y in ((153, 76), (166, 83), (179, 90)):
        painter.drawEllipse(QRectF(x - 6, y - 6, 12, 12))

    painter.end()
    if not image.save(str(OUTPUT), "ICO"):
        raise RuntimeError(f"无法写入 ICO 图标：{OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
