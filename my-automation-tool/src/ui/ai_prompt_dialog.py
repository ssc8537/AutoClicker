"""可编辑提示词文件的安全读取、只读展示与复制窗口。"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from src.core.game_keybinds import (
    GameKeybindError,
    KEYBIND_FIELDS,
    load_game_keybinds,
)
from src.core.global_hotkey import GlobalHotkeyError, load_global_hotkey
from src.core.input_keys import (
    display_input_key,
)
from src.utils.app_paths import config_root

from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtGui import QDesktopServices, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class PromptTemplateLoad:
    """一次提示词读取的结果；只用于展示，绝不执行任何文本。"""

    template: str
    current_path: Path
    default_path: Path
    notice: str = ""


@dataclass(frozen=True)
class PromptContent:
    """窗口本次显示的完整文本和其配置来源。"""

    text: str
    load: PromptTemplateLoad
    complete_path: Path | None = None


def _default_config_dir() -> Path:
    return config_root()


def _safe_template_message() -> str:
    return (
        "AI 提示词文件当前无法读取。请检查下方两个文件路径，"
        "并用默认备份人工覆盖当前文件后重新打开本窗口。"
    )


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


_STABLE_ACTION_CALLS = {
    "character_1": "player.切换(1)",
    "character_2": "player.切换(2)",
    "character_3": "player.切换(3)",
    "skill": "player.战技()",
    "echo": "player.声骸()",
    "ultimate": "player.大招()",
    "jump": "player.跳跃()",
    "execute": "player.处决()",
}


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _runtime_reference(config_dir: Path | None = None) -> str:
    """Build the current key contract from code and saved configuration."""
    root = (config_dir or _default_config_dir()).resolve()
    lines = [
        "## 10. 当前程序设置",
        "",
        "> 本节每次打开窗口时由程序动态生成，不会使用过期默认值。",
        "",
    ]
    try:
        global_hotkey = load_global_hotkey(root / "global_hotkey.ini")
        lines.append(
            "**当前全局启停键：** 内部值 "
            f"`{global_hotkey}`，界面显示 **{display_input_key(global_hotkey)}**。"
            "任何宏 `HOTKEY` 和快捷连点触发键都不能使用这个键。"
        )
    except GlobalHotkeyError as exc:
        lines.append(f"> 当前全局启停键无法读取：{exc}。不要猜测，请用户在设置页确认。")

    lines.extend(
        [
            "",
            "### 当前共享动作映射",
            "",
            "| # | 槽位 | 当前名称 | 物理键 | 显示 | 正确调用 |",
            "|---:|---|---|---|---|---|",
        ]
    )
    try:
        keybinds = load_game_keybinds(root / "game_keybinds.ini")
    except GameKeybindError as exc:
        lines.append(f"| － | 读取失败 | {_md_cell(str(exc))} | － | － | 请用户在功能页确认 |")
    else:
        for index, (slot, _default_label, _default_key) in enumerate(KEYBIND_FIELDS, 1):
            label = keybinds.label_for(slot)
            key = keybinds.key_for(slot)
            stable_call = _STABLE_ACTION_CALLS.get(slot)
            custom_call = f"player.按键({_quoted(label)})"
            calls = f"`{stable_call}` / `{custom_call}`" if stable_call else f"`{custom_call}`"
            lines.append(
                f"| {index} | `{slot}` | {_md_cell(label)} | `{key}` | "
                f"{_md_cell(display_input_key(key))} | {calls} |"
            )

    return "\n".join(lines)


def _write_complete_prompt(load: PromptTemplateLoad, text: str) -> Path | None:
    """保存程序本次实际展示的1～11节完整提示词；失败时不影响窗口。"""
    path = load.current_path.with_name("ai_prompt.complete.md")
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(path)
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    return path


def load_prompt_template(config_dir: Path | None = None) -> PromptTemplateLoad:
    """读取当前模板；只有缺失当前文件时才从默认备份恢复它。"""
    root = (config_dir or _default_config_dir()).resolve()
    current_path = root / "ai_prompt.md"
    default_path = root / "ai_prompt.default.md"
    legacy_current_path = root / "ai_prompt.txt"
    legacy_default_path = root / "ai_prompt.default.txt"
    if not current_path.exists() and legacy_current_path.exists():
        try:
            legacy_template = _read_utf8(legacy_current_path)
            current_path.write_text(legacy_template, encoding="utf-8")
        except (OSError, UnicodeError):
            pass
        else:
            return PromptTemplateLoad(
                legacy_template,
                current_path,
                default_path,
                "已从旧 TXT 提示词迁移为 Markdown；旧文件未删除。",
            )
    if not default_path.exists() and legacy_default_path.exists():
        try:
            legacy_default = _read_utf8(legacy_default_path)
        except (OSError, UnicodeError):
            legacy_default = None
        if legacy_default is not None:
            try:
                default_path.write_text(legacy_default, encoding="utf-8")
            except OSError:
                pass
    try:
        return PromptTemplateLoad(_read_utf8(current_path), current_path, default_path)
    except FileNotFoundError:
        try:
            default_template = _read_utf8(default_path)
        except (OSError, UnicodeError):
            return PromptTemplateLoad(
                _safe_template_message(),
                current_path,
                default_path,
                "当前提示词和默认备份都无法以 UTF-8 读取；没有写入任何文件。",
            )
        try:
            current_path.parent.mkdir(parents=True, exist_ok=True)
            current_path.write_text(default_template, encoding="utf-8")
        except OSError:
            return PromptTemplateLoad(
                default_template,
                current_path,
                default_path,
                "当前提示词文件缺失；已安全显示默认备份，但恢复文件失败。",
            )
        return PromptTemplateLoad(
            default_template,
            current_path,
            default_path,
            "当前提示词文件缺失，已从默认备份恢复。",
        )
    except (OSError, UnicodeError):
        try:
            default_template = _read_utf8(default_path)
        except (OSError, UnicodeError):
            return PromptTemplateLoad(
                _safe_template_message(),
                current_path,
                default_path,
                "当前提示词和默认备份都无法以 UTF-8 读取；没有写入任何文件。",
            )
        return PromptTemplateLoad(
            default_template,
            current_path,
            default_path,
            "当前提示词无法以 UTF-8 读取；已安全显示默认备份，未覆盖当前文件。",
        )


def build_ai_prompt_content(
    source: str | None = None, config_dir: Path | None = None
) -> PromptContent:
    """Append live key settings and saved source to the editable template."""
    load = load_prompt_template(config_dir)
    runtime_reference = _runtime_reference(config_dir)
    source_section = (
        "以下是已保存的完整 Python 宏源码。源码中的 Python 注释会原样保留。\n\n"
        "```python\n" + source.rstrip() + "\n```"
        if source is not None
        else "当前没有选中有效宏。请先按下面规则让 AI 返回完整文件，再粘贴到编辑器保存。"
    )
    text = (
        f"{load.template.rstrip()}\n\n{runtime_reference}\n\n"
        f"## 11. 已保存的宏源码\n\n{source_section}\n"
    )
    return PromptContent(text, load, _write_complete_prompt(load, text))


def build_ai_prompt(source: str | None = None, config_dir: Path | None = None) -> str:
    """兼容现有调用，返回本次可复制的完整纯文本提示词。"""
    return build_ai_prompt_content(source, config_dir).text


class AiPromptDialog(QDialog):
    """只读展示和复制提示词，绝不执行或导入用户宏。"""

    def __init__(
        self,
        parent: QWidget,
        prompt: str,
        template_load: PromptTemplateLoad | None = None,
        complete_path: Path | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("AI 提示词")
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setMinimumSize(720, 560)
        self.resize(820, 720)
        self.setStyleSheet(
            "QDialog { background: #FCF7FA; color: #5D4050; font-family: 'Microsoft YaHei UI', 'Microsoft YaHei'; font-size: 12px; }"
            "QTextBrowser { background: #FFFFFF; border: 1px solid #D9A9BD; border-radius: 7px; padding: 8px; selection-background-color: #C984A1; }"
            "QLabel { color: #6E4055; }"
            "QPushButton { background: #FAF3F6; border: 1px solid #C984A1; border-radius: 5px; min-height: 28px; padding: 4px 12px; color: #6E4055; font-weight: 600; }"
            "QPushButton:hover { background: #EFDDE6; border-color: #9B536F; }"
        )
        layout = QVBoxLayout(self)
        heading = QLabel("全知 AI 连招提示词 · 可拖到旁边边看边设置")
        heading.setStyleSheet("font-size: 16px; font-weight: 700; color: #8F4F68; padding: 4px;")
        layout.addWidget(heading)
        self._prompt_markdown = prompt
        self.prompt_editor = QTextBrowser()
        self.prompt_editor.setObjectName("ai_prompt_text")
        self.prompt_editor.setReadOnly(True)
        self.prompt_editor.setOpenExternalLinks(False)
        self.prompt_editor.document().setDefaultStyleSheet(
            "body { color: #553846; font-family: 'Microsoft YaHei UI'; font-size: 13px; line-height: 1.55; }"
            "h1 { color: #914F69; border-bottom: 2px solid #E3B7C8; padding-bottom: 6px; }"
            "h2 { color: #8A5368; background: #FFF3F7; padding: 6px; margin-top: 16px; }"
            "h3 { color: #6E5260; }"
            "table { border-collapse: collapse; margin: 8px 0; }"
            "th { background: #F4DDE7; color: #6E4055; padding: 5px; border: 1px solid #DAB9C6; }"
            "td { padding: 5px; border: 1px solid #E4CDD6; }"
            "code { background: #F8EEF2; color: #8B3F61; }"
            "pre { background: #2F2930; color: #FFF7FA; padding: 10px; }"
            "blockquote { color: #6D5962; background: #F9F2E9; border-left: 4px solid #E6AE72; padding: 6px; }"
        )
        self.prompt_editor.setMarkdown(prompt)
        self.prompt_editor.moveCursor(QTextCursor.MoveOperation.Start)
        layout.addWidget(self.prompt_editor, 1)
        self.path_info = QLabel("")
        self.path_info.setObjectName("ai_prompt_paths")
        self.path_info.setWordWrap(True)
        self._editable_path: Path | None = None
        self._backup_path: Path | None = None
        if template_load is not None:
            self.path_info.setText(self._path_text(template_load, complete_path))
            self._editable_path = template_load.current_path
            self._backup_path = template_load.default_path
        layout.addWidget(self.path_info)
        folder_buttons = QHBoxLayout()
        self.open_editable_folder_button = QPushButton("打开可编辑文件夹")
        self.open_editable_folder_button.setObjectName("open_editable_prompt_folder_button")
        self.open_editable_folder_button.clicked.connect(
            lambda: self._open_prompt_folder(self._editable_path)
        )
        folder_buttons.addWidget(self.open_editable_folder_button)
        self.open_backup_folder_button = QPushButton("打开备份文件存储文件夹")
        self.open_backup_folder_button.setObjectName("open_backup_prompt_folder_button")
        self.open_backup_folder_button.clicked.connect(
            lambda: self._open_prompt_folder(self._backup_path)
        )
        folder_buttons.addWidget(self.open_backup_folder_button)
        layout.addLayout(folder_buttons)
        self._sync_folder_buttons()
        self.load_status = QLabel(template_load.notice if template_load is not None else "")
        self.load_status.setObjectName("ai_prompt_load_status")
        self.load_status.setWordWrap(True)
        layout.addWidget(self.load_status)
        self.copy_status = QLabel("")
        self.copy_status.setObjectName("ai_prompt_copy_status")
        layout.addWidget(self.copy_status)
        self.copy_button = QPushButton("复制提示词")
        self.copy_button.setObjectName("copy_ai_prompt_button")
        self.copy_button.clicked.connect(self._copy_prompt)
        layout.addWidget(self.copy_button)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    @Slot()
    def _copy_prompt(self) -> None:
        QApplication.clipboard().setText(self._prompt_markdown)
        self.copy_status.setText("提示词已复制，请粘贴给 AI")

    def update_prompt(
        self,
        prompt: str,
        template_load: PromptTemplateLoad | None = None,
        complete_path: Path | None = None,
    ) -> None:
        """Refresh the modeless reader without replacing or blocking the main window."""
        self._prompt_markdown = prompt
        self.prompt_editor.setMarkdown(prompt)
        self.prompt_editor.moveCursor(QTextCursor.MoveOperation.Start)
        if template_load is not None:
            self.path_info.setText(self._path_text(template_load, complete_path))
            self._editable_path = template_load.current_path
            self._backup_path = template_load.default_path
            self._sync_folder_buttons()
            self.load_status.setText(template_load.notice)

    def _sync_folder_buttons(self) -> None:
        self.open_editable_folder_button.setEnabled(self._editable_path is not None)
        self.open_backup_folder_button.setEnabled(self._backup_path is not None)

    @staticmethod
    def _open_prompt_folder(path: Path | None) -> None:
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))

    @staticmethod
    def _path_text(
        template_load: PromptTemplateLoad, complete_path: Path | None
    ) -> str:
        complete = (
            str(complete_path)
            if complete_path is not None
            else "生成失败；请点击“复制提示词”获取程序内完整内容"
        )
        return (
            "【实时生成，只读】完整提示词（第1～11节，交给AI；每次打开都会覆盖）："
            f"{complete}\n"
            "【存储文件，可修改】规则模板（第1～9节；不会包含实时第10/11节）："
            f"{template_load.current_path}\n"
            "【存储文件，默认备份】恢复用模板（通常不要修改）："
            f"{template_load.default_path}\n"
            "修改模板后重新点击“AI 提示词”即可刷新；编辑出错时用默认备份人工覆盖。"
        )
