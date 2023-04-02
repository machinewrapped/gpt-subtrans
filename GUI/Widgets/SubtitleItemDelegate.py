import logging
from PySide6.QtCore import QModelIndex, Qt, QPoint
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget
from GUI.ProjectViewModel import SubtitleItem

from GUI.Widgets.Widgets import SubtitleItemView

class SubtitleItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.render_flags = QWidget.RenderFlag.DrawWindowBackground | QWidget.RenderFlag.DrawChildren

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        return None

    def paint(self, painter, option, index):
        if not index.isValid() or index.column() != 0:
            return super().paint(painter, option, index)

        subtitle_item = index.data(Qt.ItemDataRole.DisplayRole)
        if not isinstance(subtitle_item, SubtitleItem):
            # logging.warn(f"Index {str(index)} data not a SubtitleItem: {str(subtitle_item)}")
            return super().paint(painter, option, index)

        subtitle_item_view = SubtitleItemView(subtitle_item, parent=self.parent())
        painter.save()
        painter.translate(option.rect.topLeft())
        subtitle_item_view.setGeometry(option.rect)
        subtitle_item_view.render(painter, QPoint(0,0), renderFlags=self.render_flags)

        super().paint(painter, option, index)
        painter.restore()

    def sizeHint(self, option, index):
        if not index.isValid() or index.column() != 0:
            return super().sizeHint(option, index)

        subtitle_item = index.data(Qt.ItemDataRole.DisplayRole)
        if not isinstance(subtitle_item, SubtitleItem):
            logging.warn(f"Index {str(index)} data not a SubtitleItem: {str(subtitle_item)}")
            return super().sizeHint(option, index)

        subtitle_item_view = SubtitleItemView(subtitle_item, parent=self.parent())
        return subtitle_item_view.sizeHint()
