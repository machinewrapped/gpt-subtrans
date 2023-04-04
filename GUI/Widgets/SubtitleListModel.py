from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

from GUI.Widgets.Widgets import SubtitleItemView

class SubtitleListModel(QAbstractItemModel):
    def __init__(self, subtitles, parent=None):
        super().__init__(parent)
        self.subtitles = subtitles

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.subtitles)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.ItemDataRole.UserRole:
            return item

        if role == Qt.ItemDataRole.DisplayRole:
            return SubtitleItemView(item)
        
        if role == Qt.ItemDataRole.SizeHintRole:
            return SubtitleItemView(item).sizeHint()

        if role == Qt.ItemDataRole.UserRole:
            return self.item.subtitle_data

        return None

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() or column != 0 or row < 0 or row >= len(self.subtitles):
            return QModelIndex()

        return self.createIndex(row, column, self.subtitles[row])

    def parent(self, index):
        return QModelIndex()
