"""可编辑提示词文件的安全读取、只读展示与复制窗口。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.utils.app_paths import config_root

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPlainTextEdit,
    QPushButton,
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


def _default_config_dir() -> Path:
    return config_root()


def _safe_template_message() -> str:
    return (
        "AI 提示词文件当前无法读取。请检查下方两个文件路径，"
        "并用默认备份人工覆盖当前文件后重新打开本窗口。"
    )


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_prompt_template(config_dir: Path | None = None) -> PromptTemplateLoad:
    """读取当前模板；只有缺失当前文件时才从默认备份恢复它。"""
    root = (config_dir or _default_config_dir()).resolve()
    current_path = root / "ai_prompt.txt"
    default_path = root / "ai_prompt.default.txt"
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
    """将本次读取的模板和已保存源码拼接为仅供阅读的文本。"""
    load = load_prompt_template(config_dir)
    source_section = (
        "以下是已保存的完整 Python 宏源码。源码中的 Python 注释会原样保留。\n\n"
        + source
        if source is not None
        else "当前没有选中有效宏。请先按下面规则让 AI 返回完整文件，再粘贴到编辑器保存。"
    )
    text = f"{load.template.rstrip()}\n\n八、已保存的宏源码\n\n{source_section}\n"
    return PromptContent(text, load)


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
    ):
        super().__init__(parent)
        self.setWindowTitle("AI 提示词")
        self.setMinimumSize(620, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("可直接阅读说明，或复制后粘贴给 AI。"))
        self.prompt_editor = QPlainTextEdit(prompt)
        self.prompt_editor.setObjectName("ai_prompt_text")
        self.prompt_editor.setReadOnly(True)
        layout.addWidget(self.prompt_editor, 1)
        self.path_info = QLabel("")
        self.path_info.setObjectName("ai_prompt_paths")
        self.path_info.setWordWrap(True)
        if template_load is not None:
            self.path_info.setText(
                "用记事本修改当前提示词并保存，关闭后重新打开本窗口即可生效。\n"
                f"当前提示词：{template_load.current_path}\n"
                f"默认备份：{template_load.default_path}\n"
                "编辑出错时，请用默认备份人工覆盖当前提示词文件。"
            )
        layout.addWidget(self.path_info)
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
        QApplication.clipboard().setText(self.prompt_editor.toPlainText())
        self.copy_status.setText("提示词已复制，请粘贴给 AI")
