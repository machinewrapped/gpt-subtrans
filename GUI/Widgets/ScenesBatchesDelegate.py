from PySide6.QtWidgets import QStyledItemDelegate, QWidget
from PySide6.QtCore import Qt, QPoint

class ScenesBatchesDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.render_flags = QWidget.RenderFlag.DrawWindowBackground | QWidget.RenderFlag.DrawChildren

    def paint(self, painter, option, index):
        widget = index.data(role=Qt.ItemDataRole.DisplayRole)

        if widget is None:
            return

        self.initStyleOption(option, index)

        painter.save()
        painter.translate(option.rect.topLeft())
        widget.setGeometry(option.rect)
        widget.render(painter, QPoint(0,0), renderFlags=self.render_flags)
        painter.restore()

        super().paint(painter, option, index)

