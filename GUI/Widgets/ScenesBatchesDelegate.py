from PySide6.QtWidgets import QStyledItemDelegate, QWidget
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QRegion
from GUI.Widgets.Widgets import TreeViewItemWidget  # Import your custom widget

class ScenesBatchesDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.render_flags = QWidget.RenderFlag.DrawWindowBackground | QWidget.RenderFlag.DrawChildren

    def getTreeViewItemWidget(self, index):
        # Get the item from the index
        item = index.data(role=Qt.ItemDataRole.UserRole)
        if item is None:
            return None

        return TreeViewItemWidget(item.getContent())

    def paint(self, painter, option, index):
        widget = self.getTreeViewItemWidget(index)

        if widget is None:
            return

        painter.save()

        # Translating the painter instead of specifying the widget offset fixes the origin for the widget (why?)
        painter.translate(option.rect.topLeft())
        widget.setGeometry(option.rect)
        widget.render(painter, QPoint(0,0), renderFlags=self.render_flags)

        super().paint(painter, option, index)
        painter.restore()

    def sizeHint(self, option, index):
        widget = self.getTreeViewItemWidget(index)

        return widget.sizeHint() if widget else super().sizeHint(option, index)
