"""
统一日志模块 - 基于 Python 标准 logging 库。

特性：
- 同时输出到控制台和按日期归档的文件（logs/YYYY-MM-DD/app.log）
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
import shutil
import sys
from datetime import date, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.utils.app_paths import log_root

# 日志文件目录
_LOG_DIR = log_root()

# 默认格式
_FORMAT = logging.Formatter(
    "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

_initialized = False


def daily_log_path(day: date | None = None, log_dir: Path | None = None) -> Path:
    """返回某一天的 APP 日志路径。"""
    selected = day or date.today()
    root = Path(log_dir) if log_dir is not None else _LOG_DIR
    return root / selected.isoformat() / "app.log"


def migrate_legacy_logs(*, log_dir: Path | None = None) -> list[Path]:
    """把旧版 logs/app.log* 移到其最后修改日期目录，保留全部内容。"""
    root = Path(log_dir) if log_dir is not None else _LOG_DIR
    if not root.is_dir():
        return []
    migrated: list[Path] = []
    for source in sorted(root.glob("app.log*")):
        if not source.is_file():
            continue
        modified_day = datetime.fromtimestamp(source.stat().st_mtime).date()
        target_dir = root / modified_day.isoformat()
        target_dir.mkdir(parents=True, exist_ok=True)
        preferred = source.name if not (target_dir / source.name).exists() else f"legacy-{source.name}"
        target = target_dir / preferred
        sequence = 2
        while target.exists():
            target = target_dir / f"legacy-{sequence}-{source.name}"
            sequence += 1
        try:
            source.replace(target)
        except OSError:
            # 旧版本仍在退出或文件暂时被占用时不阻塞新程序；下次启动再迁移。
            continue
        migrated.append(target)
    return migrated


class DailyDirectoryRotatingFileHandler(logging.Handler):
    """跨午夜自动切换到日期文件夹，并在当天内部按大小轮转。"""

    def __init__(
        self,
        log_dir: Path,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 3,
    ) -> None:
        super().__init__()
        self._log_dir = Path(log_dir)
        self._max_bytes = max_bytes
        self._backup_count = backup_count
        self._active_day: date | None = None
        self._delegate: RotatingFileHandler | None = None

    def _ensure_delegate(self, day: date) -> RotatingFileHandler:
        if self._delegate is not None and self._active_day == day:
            return self._delegate
        if self._delegate is not None:
            self._delegate.close()
        path = daily_log_path(day, self._log_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        delegate = RotatingFileHandler(
            path,
            maxBytes=self._max_bytes,
            backupCount=self._backup_count,
            encoding="utf-8",
        )
        delegate.setLevel(self.level)
        if self.formatter is not None:
            delegate.setFormatter(self.formatter)
        self._delegate = delegate
        self._active_day = day
        return delegate

    def emit(self, record: logging.LogRecord) -> None:
        try:
            day = datetime.fromtimestamp(record.created).date()
            self._ensure_delegate(day).emit(record)
        except Exception:
            self.handleError(record)

    def setLevel(self, level) -> None:  # noqa: N802 - logging API 命名
        super().setLevel(level)
        if self._delegate is not None:
            self._delegate.setLevel(level)

    def setFormatter(self, formatter) -> None:  # noqa: N802 - logging API 命名
        super().setFormatter(formatter)
        if self._delegate is not None:
            self._delegate.setFormatter(formatter)

    def close(self) -> None:
        if self._delegate is not None:
            self._delegate.close()
            self._delegate = None
        super().close()


def clear_logs_older_than(
    retention_days: int, *, log_dir: Path | None = None, today: date | None = None
) -> int:
    """删除达到指定日龄的日期目录；retention_days=1 表示只保留今天。"""
    if retention_days < 1:
        raise ValueError("日志保留天数必须至少为 1")
    root = (Path(log_dir) if log_dir is not None else _LOG_DIR).resolve()
    current_day = today or date.today()
    if not root.is_dir():
        return 0
    removed_files = 0
    for child in root.iterdir():
        if child.is_dir():
            try:
                folder_day = date.fromisoformat(child.name)
            except ValueError:
                continue
            age_days = (current_day - folder_day).days
            if age_days < retention_days:
                continue
            removed_files += sum(1 for item in child.rglob("*") if item.is_file())
            shutil.rmtree(child)
    return removed_files


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

    # 默认按日期文件夹归档；显式 log_file 仅用于兼容测试/外部调用。
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    if log_file is None:
        migrate_legacy_logs(log_dir=_LOG_DIR)
        file_handler = DailyDirectoryRotatingFileHandler(_LOG_DIR)
    else:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
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
