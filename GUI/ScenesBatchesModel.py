from PySide6.QtCore import QSortFilterProxyModel, QModelIndex, Qt

from GUI.ViewModel.BatchItem import BatchItem
from GUI.ProjectViewModel import ViewModelItem
from GUI.Widgets.Widgets import TreeViewItemWidget

class ScenesBatchesModel(QSortFilterProxyModel):
    def __init__(self, viewmodel=None, parent=None):
        super().__init__(parent)
        if viewmodel:
            self.setSourceModel(viewmodel)

    def filterAcceptsRow(self, source_row : int, source_parent : QModelIndex):
        if not self.sourceModel():
            return False
        
        if not source_parent.isValid():
            return True

        item = self.sourceModel().itemFromIndex(source_parent)

        if not item or isinstance(item, BatchItem):
            return False

        return True

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        source_index = self.mapToSource(index)
        item : ViewModelItem = self.sourceModel().itemFromIndex(source_index)
        if not isinstance(item, ViewModelItem):
            return None

        if role == Qt.ItemDataRole.UserRole:
            return item

        if role == Qt.ItemDataRole.DisplayRole:
            return TreeViewItemWidget(item.GetContent())
        
        if role == Qt.ItemDataRole.SizeHintRole:
            return TreeViewItemWidget(item.GetContent()).sizeHint()

        return None
