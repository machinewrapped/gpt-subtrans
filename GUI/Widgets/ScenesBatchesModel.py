import logging
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

from GUI.ProjectViewModel import BatchItem, ViewModelItem
from GUI.Widgets.Widgets import TreeViewItemWidget

class ScenesBatchesModel(QAbstractItemModel):
    def __init__(self, viewmodel=None, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.root_item = self.viewmodel.getRootItem() if self.viewmodel else None

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return self.root_item.rowCount() if self.root_item else 0
        
        parent_item = parent.internalPointer()

        # Nothing below Batch level
        if isinstance(parent_item, BatchItem):
            return 0
        
        return parent_item.rowCount()

    def columnCount(self, parent=QModelIndex()):
        return 1

    def itemFromIndex(self, index):
        if not index.isValid():
            return None

        item = index.internalPointer()
        return item

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        item : ViewModelItem = index.internalPointer()

        if role == Qt.ItemDataRole.UserRole:
            return item

        if role == Qt.ItemDataRole.DisplayRole:
            return TreeViewItemWidget(item.GetContent())
        
        if role == Qt.ItemDataRole.SizeHintRole:
            return TreeViewItemWidget(item.GetContent()).sizeHint()

        return None

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            child_item = self.root_item.child(row)
        else:
            parent_item = parent.internalPointer()
            child_item = parent_item.child(row)

        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)
