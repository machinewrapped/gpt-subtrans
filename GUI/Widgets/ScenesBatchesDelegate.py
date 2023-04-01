from PySide6.QtWidgets import QStyledItemDelegate, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QRegion
from GUI.ProjectViewModel import BatchItem, SceneItem
from GUI.Widgets.TreeItem import TreeItemWidget
from GUI.Widgets.Widgets import TreeViewItemWidget  # Import your custom widget

class ScenesBatchesDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

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

        render_flags = QWidget.RenderFlag.DrawWindowBackground | QWidget.RenderFlag.DrawChildren
        widget.setGeometry(option.rect)
        widget.render(painter, option.rect.topLeft(), renderFlags=render_flags)

        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        widget = self.getTreeViewItemWidget(index)

        return widget.sizeHint() if widget else super().sizeHint(option, index)
