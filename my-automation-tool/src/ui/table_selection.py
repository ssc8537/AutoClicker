"""表格选中时保留单元格自己的状态文字颜色。"""
from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor, QPalette
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem


class PreserveForegroundSelectionDelegate(QStyledItemDelegate):
    """淡蓝选中背景不覆盖红、绿、紫等 ForegroundRole。"""

    @staticmethod
    def option_for_index(
        option: QStyleOptionViewItem, index: QModelIndex
    ) -> QStyleOptionViewItem:
        prepared = QStyleOptionViewItem(option)
        foreground = index.data(Qt.ItemDataRole.ForegroundRole)
        if prepared.state & QStyle.StateFlag.State_Selected:
            if foreground is None:
                foreground = prepared.palette.brush(QPalette.ColorRole.Text)
            if isinstance(foreground, QColor):
                foreground = QBrush(foreground)
            if isinstance(foreground, QBrush):
                palette = QPalette(prepared.palette)
                palette.setBrush(QPalette.ColorRole.HighlightedText, foreground)
                prepared.palette = palette
        return prepared

    def paint(self, painter, option, index) -> None:
        super().paint(painter, self.option_for_index(option, index), index)
