"""源码运行与 Windows 便携版共用的资源、数据目录。"""
from __future__ import annotations

from pathlib import Path
import sys


def application_root() -> Path:
    """返回用户可写的程序根目录，不使用 PyInstaller 临时目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_root() -> Path:
    """返回只读打包资源目录；源码模式与程序根相同。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return application_root()


def macro_root() -> Path:
    return application_root() / "macros"


def config_root() -> Path:
    return application_root() / "config"


def log_root() -> Path:
    return application_root() / "logs"
