"""源码运行与 Windows 便携版共用的资源、数据目录。"""
from __future__ import annotations

from pathlib import Path
import sys


def application_root() -> Path:
    """返回用户可写的程序根目录，不使用 PyInstaller 临时目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def data_root() -> Path:
    """Return the writable macro/config root, including this checkout's dist build."""
    root = application_root()
    if not getattr(sys, "frozen", False):
        return root
    # A development build lives in ``project/dist/MyAutoPlayer`` while the
    # user's long-lived macros and editable prompt remain in ``project``.
    # A separately copied portable app has no such project root and continues
    # to keep its data next to the executable.
    candidate = root.parent.parent
    if (candidate / "macros").is_dir() or (candidate / "config").is_dir():
        return candidate
    return root


def resource_root() -> Path:
    """返回只读打包资源目录；源码模式与程序根相同。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return application_root()


def macro_root() -> Path:
    return data_root() / "macros"


def config_root() -> Path:
    return data_root() / "config"


def log_root() -> Path:
    return data_root() / "logs"


def capture_root() -> Path:
    """开发连招的默认视频与会话目录。"""
    return data_root() / "captures"
