from PySide6.QtCore import QModelIndex, Qt, QPoint
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget

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

        widget = index.data(Qt.ItemDataRole.DisplayRole)
        if not isinstance(widget, SubtitleItemView):
            return super().paint(painter, option, index)

        self.initStyleOption(option, index)

        painter.save()
        painter.translate(option.rect.topLeft())
        widget.setGeometry(option.rect)
        widget.render(painter, QPoint(0,0), renderFlags=self.render_flags)
        painter.restore()

        super().paint(painter, option, index)
