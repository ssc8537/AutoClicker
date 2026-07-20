"""从用户角色原图生成更饱满的窗口、任务栏、EXE 和托盘共用 ICO。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "myautoplayer-icon-source.png"
OUTPUT = ROOT / "assets" / "myautoplayer.ico"
ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)


def enlarged_square(source: Image.Image) -> Image.Image:
    """轻裁左右与底部约 3%，保留顶部头发和右侧发卡。"""
    image = source.convert("RGBA")
    side = min(image.size)
    cropped_side = round(side * 0.97)
    left = max(0, (image.width - cropped_side) // 2)
    top = 0
    right = left + cropped_side
    bottom = top + cropped_side
    return image.crop((left, top, right, bottom))


def main() -> int:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"缺少用户角色图标源文件：{SOURCE}")
    with Image.open(SOURCE) as source:
        prepared = enlarged_square(source)
        master = prepared.resize((256, 256), Image.Resampling.LANCZOS)
        master.save(OUTPUT, format="ICO", sizes=[(size, size) for size in ICON_SIZES])
    print(f"已生成统一图标：{OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
