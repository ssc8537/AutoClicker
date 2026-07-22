"""Stage 2A 的受控 Python 宏文件管理；所有校验均为静态 AST 校验。"""
from __future__ import annotations

import os
import ctypes
from ctypes import wintypes
from pathlib import Path
from uuid import uuid4

from src.core.macro_library import (
    replace_name_metadata,
    replace_trigger_metadata,
    validate_macro_source,
)


class MacroFileError(ValueError):
    """用户可修正的宏文件管理失败。"""


DEFAULT_MACRO_TEMPLATE = '''NAME = {name!r}
HOTKEY = "f1"
MODE = "down"
COUNT = 1
SPEED = 1.0
ENABLED = True


def run(player):
    pass
'''

_INVALID_WINDOWS_NAME_CHARS = set('<>:"/\\|?*')
_WINDOWS_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}


class MacroFileManager:
    """仅管理项目宏根目录中的顶层 UTF-8 Python 文件。"""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def template_source(self, name: str) -> str:
        return DEFAULT_MACRO_TEMPLATE.format(name=self.normalize_name(name))

    def create(self, name: str, source: str | None = None) -> Path:
        normalized = self.normalize_name(name)
        target = self._target_path(normalized)
        self._ensure_root()
        self._ensure_available(target)
        candidate = self._with_name(
            source if source is not None else self.template_source(normalized), normalized, target
        )
        self._validate(candidate, target)
        self._atomic_write(target, candidate)
        return target

    def update(
        self,
        path: str | Path,
        name: str,
        source: str,
        *,
        active_path: str | Path | None = None,
    ) -> Path:
        current = self._owned_existing_path(path)
        # 已启用宏也可保存。当前运行轮次持有 F9 启动时的 PythonMacro 快照，
        # 此处的文件事务只会影响下一次 F9 reload。
        normalized = self.normalize_name(name)
        target = self._target_path(normalized)
        self._ensure_available(target, current=current)
        candidate = self._with_name(source, normalized, target)
        self._validate(candidate, target)
        if target.name.casefold() == current.name.casefold():
            self._atomic_write(current, candidate)
            return current
        self._rename_with_atomic_content(current, target, candidate)
        return target

    def rename(
        self,
        path: str | Path,
        name: str,
        *,
        active_path: str | Path | None = None,
    ) -> Path:
        current = self._owned_existing_path(path)
        return self.update(current, name, self.read_source(current), active_path=active_path)

    def update_trigger_settings(
        self,
        path: str | Path,
        *,
        hotkey: str,
        mode: str,
        count: int,
        speed: float,
        enabled: bool,
    ) -> None:
        """由触发页即时保存元数据，用户动作代码保持原样。"""
        current = self._owned_existing_path(path)
        try:
            source = self.read_source(current)
            candidate = replace_trigger_metadata(
                source,
                hotkey=hotkey,
                mode=mode,
                count=count,
                speed=speed,
                enabled=enabled,
                filename=str(current),
            )
        except ValueError as exc:
            raise MacroFileError(str(exc)) from exc
        self._atomic_write(current, candidate)

    def read_source(self, path: str | Path) -> str:
        current = self._owned_existing_path(path)
        try:
            return current.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            raise MacroFileError("无法读取 Python 宏文件") from exc

    def move_to_recycle_bin(self, path: str | Path) -> None:
        """将受控宏送入 Windows 回收站，绝不退化为永久删除。"""
        current = self._owned_existing_path(path)
        try:
            _move_to_windows_recycle_bin(current)
        except OSError as exc:
            raise MacroFileError("删除失败，文件仍保留在宏目录") from exc

    def normalize_name(self, name: str) -> str:
        candidate = name.strip()
        if candidate.lower().endswith(".py"):
            candidate = candidate[:-3].strip()
        if not candidate or candidate in {".", ".."}:
            raise MacroFileError("名称不能为空")
        if candidate.endswith((".", " ")) or any(
            character in _INVALID_WINDOWS_NAME_CHARS or ord(character) < 32
            for character in candidate
        ):
            raise MacroFileError("名称包含 Windows 不允许的字符")
        if candidate.split(".", 1)[0].casefold() in _WINDOWS_RESERVED_NAMES:
            raise MacroFileError("名称是 Windows 保留名称")
        return candidate

    def _ensure_root(self) -> None:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise MacroFileError("无法创建宏目录") from exc

    def _target_path(self, name: str) -> Path:
        return self.root / f"{name}.py"

    def _owned_existing_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        try:
            if candidate.parent.resolve() != self.root.resolve():
                raise MacroFileError("只能管理宏目录中的顶层 Python 文件")
        except OSError as exc:
            raise MacroFileError("无法确认宏文件位置") from exc
        if candidate.suffix.lower() != ".py" or candidate.is_symlink() or not candidate.is_file():
            raise MacroFileError("只能管理存在的普通 Python 宏文件")
        return candidate

    def _ensure_available(self, target: Path, *, current: Path | None = None) -> None:
        for path in self.root.glob("*.py") if self.root.is_dir() else ():
            if path.name.casefold() == target.name.casefold() and path != current:
                raise MacroFileError("已有同名 Python 宏")

    @staticmethod
    def _validate(source: str, target: Path) -> None:
        try:
            validate_macro_source(source, filename=str(target))
        except ValueError as exc:
            raise MacroFileError(str(exc)) from exc

    @staticmethod
    def _with_name(source: str, name: str, target: Path) -> str:
        try:
            return replace_name_metadata(source, name, filename=str(target))
        except ValueError as exc:
            raise MacroFileError(str(exc)) from exc

    @staticmethod
    def _atomic_write(target: Path, source: str) -> None:
        temporary = MacroFileManager._write_validated_temp(target, source)
        try:
            os.replace(temporary, target)
        except OSError as exc:
            raise MacroFileError("保存失败，原文件未被覆盖") from exc
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    @staticmethod
    def _write_validated_temp(target: Path, source: str) -> Path:
        temporary = target.parent / f".{target.name}.{uuid4().hex}.tmp"
        try:
            temporary.write_text(source, encoding="utf-8", newline="\n")
            validate_macro_source(temporary.read_text(encoding="utf-8"), filename=str(target))
        except (OSError, UnicodeError, ValueError) as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise MacroFileError("保存失败，原文件未被覆盖") from exc
        return temporary

    @staticmethod
    def _rename_with_atomic_content(current: Path, target: Path, source: str) -> None:
        """先隐藏旧文件，再原子放入新文件；失败时恢复旧路径。"""
        temporary = MacroFileManager._write_validated_temp(target, source)
        backup = current.parent / f".{current.name}.{uuid4().hex}.bak"
        old_moved = False
        try:
            os.replace(current, backup)
            old_moved = True
            os.replace(temporary, target)
            old_moved = False
        except OSError as exc:
            if old_moved:
                try:
                    os.replace(backup, current)
                except OSError:
                    pass
            raise MacroFileError("重命名失败，已尝试恢复旧文件") from exc
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            if target.exists():
                try:
                    backup.unlink(missing_ok=True)
                except OSError:
                    pass


class _SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", ctypes.c_ushort),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    ]


def _move_to_windows_recycle_bin(path: Path) -> None:
    """调用 Shell 回收站移动；供文件服务和测试共同使用。"""
    if os.name != "nt":
        raise OSError("此功能仅支持 Windows 回收站")
    operation = _SHFILEOPSTRUCTW()
    operation.wFunc = 3  # FO_DELETE
    operation.pFrom = str(path) + "\0\0"
    operation.fFlags = 0x0040 | 0x0010 | 0x0400  # ALLOWUNDO | NOCONFIRMATION | NOERRORUI
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
    if result != 0 or operation.fAnyOperationsAborted:
        raise OSError(f"Windows 回收站操作失败：{result}")


def move_path_to_windows_recycle_bin(path: str | Path) -> None:
    """Public shared entry point for guarded services that recycle owned paths."""
    _move_to_windows_recycle_bin(Path(path))
