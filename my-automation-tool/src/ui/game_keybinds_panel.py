"""Stage 3K 设置页的共享键位编辑区域。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from src.core.game_keybinds import (
    KEYBIND_FIELDS,
    GameKeybindError,
    GameKeybinds,
    load_game_keybinds,
    save_game_keybinds,
)
from src.ui.trigger_key_edit import TriggerKeyEdit


class GameKeybindsPanel(QWidget):
    """编辑全部宏共享的键盘映射，不注册任何额外热键。"""

    def __init__(self, config_path: Path | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self._config_path = config_path
        self._fields: dict[str, TriggerKeyEdit] = {}
        self._label_fields: dict[str, QLineEdit] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)
        for name, label, _ in KEYBIND_FIELDS:
            field = TriggerKeyEdit()
            field.setObjectName(f"game_keybind_{name}")
            self._fields[name] = field
            name_field = QLineEdit()
            name_field.setObjectName(f"game_keybind_label_{name}")
            name_field.setMaxLength(24)
            name_field.setPlaceholderText(label)
            self._label_fields[name] = name_field
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)
            row_layout.addWidget(name_field, 1)
            row_layout.addWidget(field, 1)
            form.addRow(label, row)
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
        self.setMinimumHeight(max(self.sizeHint().height(), len(KEYBIND_FIELDS) * 34 + 80))

    def _load(self) -> None:
        try:
            keybinds = load_game_keybinds(self._config_path)
        except GameKeybindError as exc:
            self._notice.setText(f"现有键位配置无效，尚未覆盖：{exc}")
            keybinds = GameKeybinds({name: default for name, _, default in KEYBIND_FIELDS})
        else:
            self._notice.setText("左框可改动作名称，右框点击后录入按键；所有动作允许使用同一个键。")
        self._show(keybinds)

    def _show(self, keybinds: GameKeybinds) -> None:
        for name, field in self._fields.items():
            field.set_hotkey(keybinds.key_for(name))
        for name, field in self._label_fields.items():
            field.setText(keybinds.label_for(name))

    def _save(self) -> None:
        try:
            keybinds = GameKeybinds(
                {name: field.hotkey() for name, field in self._fields.items()},
                {name: field.text() for name, field in self._label_fields.items()},
            )
            save_game_keybinds(keybinds, self._config_path)
        except GameKeybindError as exc:
            self._notice.setText(f"保存失败：{exc}")
            return
        self._show(keybinds)
        self._notice.setText("名称和键位已保存。Python 宏可用 player.按键(\"动作名称\") 调用。")
