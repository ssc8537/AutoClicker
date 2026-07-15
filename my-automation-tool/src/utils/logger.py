"""
统一日志模块 - 基于 Python 标准 logging 库。

特性：
- 同时输出到控制台和文件（logs/app.log）
- 支持 DEBUG / INFO / WARNING / ERROR 四个级别
- 线程安全（logging 模块内置）
- 每个模块通过 get_logger(__name__) 获取独立 logger

用法：
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("程序启动")
    logger.error("发生异常", exc_info=True)
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 日志文件目录
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "app.log"

# 默认格式
_FORMAT = logging.Formatter(
    "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

_initialized = False


def setup_logging(level: int = logging.INFO, log_file: str = None):
    """初始化全局日志配置（仅需调用一次）"""
    global _initialized
    if _initialized:
        return
    _initialized = True

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(_FORMAT)
    root_logger.addHandler(console)

    # 文件 handler（带轮转，最大 5MB，保留 3 个备份）
    file_path = log_file or str(_LOG_FILE)
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # 文件记录全部级别
    file_handler.setFormatter(_FORMAT)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger 实例"""
    if not _initialized:
        setup_logging()
    return logging.getLogger(name)
