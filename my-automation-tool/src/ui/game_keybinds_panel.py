"""Stage 3K 设置页的共享键位编辑区域。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFormLayout, QLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from src.core.game_keybinds import (
    KEYBIND_FIELDS,
    GameKeybindError,
    GameKeybinds,
    display_key,
    load_game_keybinds,
    save_game_keybinds,
)


class GameKeybindsPanel(QWidget):
    """编辑全部宏共享的键盘映射，不注册任何额外热键。"""

    def __init__(self, config_path: Path | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self._config_path = config_path
        self._fields: dict[str, QLineEdit] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)
        for name, label, _ in KEYBIND_FIELDS:
            field = QLineEdit()
            field.setObjectName(f"game_keybind_{name}")
            field.setMaxLength(24)
            self._fields[name] = field
            form.addRow(label, field)
        layout.addLayout(form)
        self._save_button = QPushButton("保存键位设置")
        self._save_button.setObjectName("save_game_keybinds_button")
        self._save_button.clicked.connect(self._save)
        layout.addWidget(self._save_button)
        self._notice = QLabel()
        self._notice.setObjectName("game_keybind_notice")
        self._notice.setWordWrap(True)
        layout.addWidget(self._notice)
        self._load()
        # 外层设置表单位于滚动区域内；显式保留自然高度，避免八行字段被压成细线。
        self.setMinimumHeight(max(self.sizeHint().height(), len(KEYBIND_FIELDS) * 30 + 80))

    def _load(self) -> None:
        try:
            keybinds = load_game_keybinds(self._config_path)
        except GameKeybindError as exc:
            self._notice.setText(f"现有键位配置无效，尚未覆盖：{exc}")
            keybinds = GameKeybinds({name: default for name, _, default in KEYBIND_FIELDS})
        else:
            self._notice.setText("仅影响已启用宏的中文语义键盘接口；F2/F9/F12 不可配置。")
        self._show(keybinds)

    def _show(self, keybinds: GameKeybinds) -> None:
        for name, field in self._fields.items():
            field.setText(display_key(keybinds.key_for(name)))

    def _save(self) -> None:
        try:
            keybinds = GameKeybinds({name: field.text() for name, field in self._fields.items()})
            save_game_keybinds(keybinds, self._config_path)
        except GameKeybindError as exc:
            self._notice.setText(f"保存失败：{exc}")
            return
        self._show(keybinds)
        self._notice.setText("键位设置已保存；下一次宏执行会使用新映射（重新按 F9 最明确）。")
