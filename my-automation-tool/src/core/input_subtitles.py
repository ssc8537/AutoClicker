"""把录像会话的物理按键边沿转换为可叠加的 ASS 字幕雏形。"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Iterable, Mapping


@dataclass
class _KeyCycle:
    hotkey: str
    physical_name: str
    start_ms: float
    up_ms: float | None = None
    held_ms: float | None = None
    release_ms: float | None = None
    still_held_at_end: bool = False
    release_measured_to_end: bool = False


def write_input_subtitles(
    target: Path,
    records: Iterable[Mapping[str, object]],
    *,
    session_end_ms: float,
    srt_target: Path | None = None,
) -> int:
    """生成两行按键卡片：物理键名；按下毫秒与松开毫秒。"""
    cycles = _build_cycles(records, max(0.0, float(session_end_ms)))
    lines = _ass_header()
    snapshots = _snapshots(cycles, session_end_ms)
    for start_ms, visible_end, visible_cycles in snapshots:
        panel_width = 1120
        panel_height = 42 + len(visible_cycles) * 92
        panel_left = (1920 - panel_width) // 2
        # 播放器的底部控制栏常会覆盖视频下方约120px（720p）。
        # 在1920×1080字幕坐标中预留200px安全距离，三组信息整体
        # 向屏幕中心靠近，无需用户再手动上拖。
        panel_top = 1080 - 200 - panel_height
        panel_shape = (
            f"m 0 0 l {panel_width} 0 l {panel_width} {panel_height} "
            f"l 0 {panel_height}"
        )
        # 背景使用独立矢量图层，不依赖播放器对 BorderStyle=3
        # “文字背景”的不完整实现。深色画面也能看到淡梅色面板边界。
        lines.append(
            "Dialogue: "
            f"0,{_ass_time(start_ms, floor=True)},"
            f"{_ass_time(visible_end, floor=True)},KeyPanel,,0,0,0,,"
            rf"{{\an7\pos({panel_left},{panel_top})\p1\1c&H006F5A7D&"
            rf"\1a&H40&\3c&H0030202A&\3a&H00&\bord3\shad0}}{panel_shape}"
        )
        cards: list[str] = []
        for index, cycle in enumerate(visible_cycles):
            title, detail = _card_lines(cycle)
            newest = index == len(visible_cycles) - 1
            title_colour = "&H00E8D4FF&" if newest else "&H00F0E6D8&"
            cards.append(
                rf"{{\fs40\b1\c{title_colour}}}按键：{_escape_ass(title)}"
                rf"\N{{\fs29\b0\c&H00FFFFFF&}}{_escape_ass(detail)}"
            )
        text = r"\N".join(cards)
        lines.append(
            "Dialogue: "
            f"1,{_ass_time(start_ms, floor=True)},"
            f"{_ass_time(visible_end, floor=True)},KeyText,,0,0,0,,"
            rf"{{\an8\pos(960,{panel_top + 20})\bord6\shad2}}{text}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8-sig", newline="\n")
    if srt_target is not None:
        _write_srt(srt_target, cycles, session_end_ms)
    return len(cycles)


def _build_cycles(
    records: Iterable[Mapping[str, object]], session_end_ms: float
) -> list[_KeyCycle]:
    pending: dict[str, tuple[float, str]] = {}
    last_completed: dict[str, _KeyCycle] = {}
    cycles: list[_KeyCycle] = []
    for record in records:
        state = str(record.get("state", ""))
        hotkey = str(record.get("hotkey", ""))
        if not hotkey or state not in {"down", "up"}:
            continue
        relative_ms = _number(record.get("relative_ms"))
        if relative_ms is None:
            continue
        physical_name = str(record.get("physical_name") or hotkey)
        if state == "down":
            previous = last_completed.get(hotkey)
            if previous is not None and previous.up_ms is not None and previous.release_ms is None:
                previous.release_ms = max(0.0, relative_ms - previous.up_ms)
            pending.setdefault(hotkey, (relative_ms, physical_name))
            continue
        pressed = pending.pop(hotkey, None)
        if pressed is None:
            continue
        start_ms, down_name = pressed
        held_ms = _number(record.get("held_ms"))
        if held_ms is None:
            held_ms = max(0.0, relative_ms - start_ms)
        cycle = _KeyCycle(
            hotkey,
            down_name,
            start_ms,
            up_ms=relative_ms,
            held_ms=held_ms,
        )
        cycles.append(cycle)
        last_completed[hotkey] = cycle

    for hotkey, (start_ms, physical_name) in pending.items():
        cycles.append(
            _KeyCycle(
                hotkey,
                physical_name,
                start_ms,
                held_ms=max(0.0, session_end_ms - start_ms),
                still_held_at_end=True,
            )
        )
    for cycle in cycles:
        if cycle.up_ms is not None and cycle.release_ms is None:
            cycle.release_ms = max(0.0, session_end_ms - cycle.up_ms)
            cycle.release_measured_to_end = True
    cycles.sort(key=lambda item: item.start_ms)
    return cycles


def _ass_header() -> list[str]:
    return [
        "[Script Info]",
        "Title: MyAutoPlayer Input Subtitles",
        "ScriptType: v4.00+",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "YCbCr Matrix: TV.709",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: KeyPanel,Microsoft YaHei UI,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        "Style: KeyText,Microsoft YaHei UI,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,2,8,45,45,35,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]


def _write_srt(target: Path, cycles: list[_KeyCycle], session_end_ms: float) -> None:
    lines: list[str] = []
    for index, (start_ms, visible_end, visible_cycles) in enumerate(
        _snapshots(cycles, session_end_ms), 1
    ):
        lines.extend(
            [
                str(index),
                f"{_srt_time(start_ms)} --> {_srt_time(visible_end)}",
            ]
        )
        for cycle in visible_cycles:
            title, detail = _card_lines(cycle)
            lines.extend([f"按键：{title}", detail])
        lines.append("")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8-sig", newline="\n")


def _card_lines(cycle: _KeyCycle) -> tuple[str, str]:
    held = "—" if cycle.held_ms is None else f"{cycle.held_ms:.1f} ms"
    if cycle.still_held_at_end:
        released = "—（录像结束仍按住）"
    elif cycle.release_ms is None:
        released = "—"
    else:
        suffix = "（至录像结束）" if cycle.release_measured_to_end else ""
        released = f"{cycle.release_ms:.1f} ms{suffix}"
    return cycle.physical_name, f"按下 {held}  ·  分开 {released}"


def _snapshots(
    cycles: list[_KeyCycle], session_end_ms: float
) -> list[tuple[float, float, list[_KeyCycle]]]:
    """一个时间点只显示一个面板，并对齐ASS的10ms时基。

    多个按键若落在同一个百分秒内，只生成一个最新快照；这样不会因
    起止时间取整而在播放器中再次重叠。每个按键的真实毫秒数仍保留在文本中。
    """
    grouped: list[tuple[float, int]] = []
    for index, cycle in enumerate(cycles):
        start_ms = math.ceil(max(0.0, cycle.start_ms) / 10.0) * 10.0
        if grouped and grouped[-1][0] == start_ms:
            grouped[-1] = (start_ms, index)
        else:
            grouped.append((start_ms, index))

    snapshots: list[tuple[float, float, list[_KeyCycle]]] = []
    for group_index, (start_ms, cycle_index) in enumerate(grouped):
        if group_index + 1 < len(grouped):
            visible_end = min(grouped[group_index + 1][0], start_ms + 2000.0)
        else:
            visible_end = max(
                start_ms + 200.0,
                min(
                    math.ceil(max(0.0, session_end_ms + 100.0) / 10.0) * 10.0,
                    start_ms + 2000.0,
                ),
            )
        snapshots.append(
            (
                start_ms,
                visible_end,
                cycles[max(0, cycle_index - 2) : cycle_index + 1],
            )
        )
    return snapshots


def _ass_time(milliseconds: float, *, floor: bool) -> str:
    centiseconds = (
        math.floor(max(0.0, milliseconds) / 10.0)
        if floor
        else math.ceil(max(0.0, milliseconds) / 10.0)
    )
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    seconds, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def _srt_time(milliseconds: float) -> str:
    total = max(0, round(milliseconds))
    hours, remainder = divmod(total, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _escape_ass(value: str) -> str:
    return value.replace("\\", "／").replace("{", "（").replace("}", "）").replace("\n", " ")
