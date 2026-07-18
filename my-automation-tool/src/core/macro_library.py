"""C1 受控 Python 宏发现与静态校验，不执行宏文件。"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class MacroMetadata:
    """仅供宏库显示和活动状态使用的静态元数据。"""

    name: str
    hotkey: str
    mode: str
    count: int
    speed: float


@dataclass(frozen=True)
class MacroEntry:
    path: Path
    macro: MacroMetadata | None
    error: str | None = None

    @property
    def valid(self) -> bool:
        return self.macro is not None


def scan_macro_root(root: str | Path) -> list[MacroEntry]:
    root_path = Path(root)
    if not root_path.is_dir():
        return []
    entries: list[MacroEntry] = []
    for path in sorted(root_path.iterdir(), key=lambda item: item.name.lower()):
        if (
            not path.is_file()
            or path.is_symlink()
            or path.suffix.lower() != ".py"
            or path.name == "__init__.py"
            or path.name.startswith((".", "~"))
        ):
            continue
        try:
            entries.append(MacroEntry(path, _read_static_metadata(path)))
        except ValueError as exc:
            entries.append(MacroEntry(path, None, str(exc)))
    return entries


def _read_static_metadata(path: Path) -> MacroMetadata:
    """解析固定接口；绝不导入或执行不可信宏源码。"""
    try:
        source = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise ValueError(f"Python 宏语法或读取失败: {exc}") from exc
    return validate_macro_source(source, filename=str(path))


def validate_macro_source(source: str, *, filename: str = "<Python 宏>") -> MacroMetadata:
    """静态校验 Python 宏源码；绝不导入或执行源码。"""
    try:
        module = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise ValueError(f"Python 宏语法或读取失败: {exc}") from exc

    values: dict[str, object] = {}
    run_nodes: list[ast.FunctionDef] = []
    metadata_names = {"NAME", "HOTKEY", "MODE", "COUNT", "SPEED"}
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            run_nodes.append(node)
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
        for target in targets:
            if isinstance(target, ast.Name) and target.id in metadata_names:
                try:
                    values[target.id] = ast.literal_eval(value)
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"{target.id} 必须是字面量") from exc

    name = values.get("NAME")
    hotkey = values.get("HOTKEY")
    mode = values.get("MODE")
    count = values.get("COUNT")
    speed = values.get("SPEED")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("NAME 必须是非空字符串")
    if hotkey != "f9":
        raise ValueError("阶段 3 的 HOTKEY 必须是 'f9'")
    if mode not in {"switch", "down"}:
        raise ValueError("MODE 必须是 'switch' 或 'down'")
    if not _is_int(count) or not 0 <= count <= 99:
        raise ValueError("COUNT 必须是 0 至 99 的整数")
    if not _is_number(speed) or not 0.01 <= float(speed) <= 8.0:
        raise ValueError("SPEED 必须是 0.01 至 8.0 的数字")
    _validate_run_signature(run_nodes)
    return MacroMetadata(name, hotkey, mode, count, float(speed))


def replace_name_metadata(source: str, name: str, *, filename: str = "<Python 宏>") -> str:
    """只替换顶层 NAME 字面量，保留用户其余代码与格式。"""
    try:
        module = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise ValueError(f"Python 宏语法或读取失败: {exc}") from exc
    for node in module.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
        if any(isinstance(target, ast.Name) and target.id == "NAME" for target in targets):
            if value is None or not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                raise ValueError("NAME 必须是字符串字面量")
            start = _source_offset(source, value.lineno, value.col_offset)
            end = _source_offset(source, value.end_lineno, value.end_col_offset)
            return f"{source[:start]}{name!r}{source[end:]}"
    raise ValueError("NAME 必须是非空字符串")


def _validate_run_signature(run_nodes: list[ast.FunctionDef]) -> None:
    if not run_nodes:
        raise ValueError("必须定义 run(player) 函数")
    if len(run_nodes) != 1:
        raise ValueError("必须且只能定义 run(player) 函数")
    arguments = run_nodes[0].args
    if (
        arguments.posonlyargs
        or len(arguments.args) != 1
        or arguments.args[0].arg != "player"
        or arguments.vararg is not None
        or arguments.kwonlyargs
        or arguments.kwarg is not None
        or arguments.defaults
        or arguments.kw_defaults
    ):
        raise ValueError("run 必须精确为 run(player)")


def _source_offset(source: str, line_number: int, column: int) -> int:
    lines = source.splitlines(keepends=True)
    # ast 的 col_offset/end_col_offset 是 UTF-8 字节偏移；Python 字符串切片则按字符。
    # 将当前行的字节偏移还原为字符长度，才能安全替换中文 NAME 字面量。
    prefix = lines[line_number - 1].encode("utf-8")[:column].decode("utf-8")
    return sum(len(line) for line in lines[: line_number - 1]) + len(prefix)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
