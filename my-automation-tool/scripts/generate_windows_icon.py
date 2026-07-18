"""把项目自制 SVG 转为 Windows EXE 使用的 ICO 图标。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "myautoplayer-pink.svg"
OUTPUT = ROOT / "assets" / "myautoplayer-pink.ico"


def main() -> int:
    renderer = QSvgRenderer(str(SOURCE))
    if not renderer.isValid():
        raise RuntimeError(f"无法读取 SVG 图标：{SOURCE}")
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    if not image.save(str(OUTPUT), "ICO"):
        raise RuntimeError(f"无法写入 ICO 图标：{OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
