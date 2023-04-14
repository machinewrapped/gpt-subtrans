import logging
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from GUI.ProjectViewModel import BatchItem, ProjectViewModel, SceneItem, SubtitleItem
from GUI.ProjectSelection import ProjectSelection
from GUI.Widgets.Widgets import SubtitleItemView

class SubtitleListModel(QAbstractItemModel):
    def __init__(self, show_translated, viewmodel=None, parent=None):
        super().__init__(parent)
        self.show_translated = show_translated
        self.viewmodel : ProjectViewModel = viewmodel
        self.visible = []

    def ShowSelectedBatches(self, selection : ProjectSelection):
        visible = []
        viewmodel = self.viewmodel
        selected_batch_numbers = selection.batch_numbers
        root_item = viewmodel.getRootItem()
        for scene_index in range(0, root_item.rowCount()):
            scene_item : SceneItem = root_item.child(scene_index, 0)
            for batch_index in range (0, scene_item.rowCount()):
                batch_item : BatchItem = scene_item.child(batch_index, 0)
                
                show = (scene_item.number, batch_item.number) in selected_batch_numbers

                if show:
                    subtitles = batch_item.translated if self.show_translated else batch_item.subtitles
                    logging.info(f"Scene {scene_item.number} batch {batch_item.number} has {len(subtitles)} lines")
                    visible_lines = [ (scene_item.number, batch_item.number, line) for line in subtitles.keys() ]
                    visible.extend(visible_lines)
        
        self.visible = visible
        self.layoutChanged.emit()

    def rowCount(self, parent=QModelIndex()):
        return len(self.visible)

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

        return None

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() or column != 0 or row < 0 or row >= self.rowCount():
            return QModelIndex()
        
        scene_number, batch_number, line_number = self.visible[row]
        batches : list[BatchItem] = self.viewmodel.model[scene_number].batches
        subtitles = batches[batch_number].translated if self.show_translated else batches[batch_number].subtitles
        subtitle : SubtitleItem = subtitles [line_number]
        return self.createIndex(row, column, subtitle)

    def parent(self, index):
        return QModelIndex()
