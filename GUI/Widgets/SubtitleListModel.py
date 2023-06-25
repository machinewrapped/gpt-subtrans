import logging
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from GUI.ProjectViewModel import BatchItem, ProjectViewModel, SceneItem, LineItem
from GUI.ProjectSelection import ProjectSelection
from GUI.Widgets.Widgets import LineItemView

class SubtitleListModel(QAbstractItemModel):
    def __init__(self, show_translated, viewmodel=None, parent=None):
        super().__init__(parent)
        self.show_translated = show_translated
        self.viewmodel : ProjectViewModel = viewmodel
        self.selected_batch_numbers = []
        self.visible = []

        # self.viewmodel.layoutChanged.connect(self._update_visible_batches)
<<<<<<< HEAD
        # self.viewmodel.layoutChanged.connect(self._reset_visible_batches)
=======
>>>>>>> main

    def ShowSelection(self, selection : ProjectSelection):
        if selection.selected_batches:
            batch_numbers = [(batch.scene, batch.number) for batch in selection.selected_batches]
        elif selection.selected_scenes:
            batch_numbers = selection.batch_numbers
        else:
            batch_numbers = self.viewmodel.GetBatchNumbers()

        self.ShowSelectedBatches(batch_numbers)

    def ShowSelectedBatches(self, batch_numbers):
        self.selected_batch_numbers = batch_numbers
        viewmodel = self.viewmodel
        visible = []

        root_item = viewmodel.getRootItem()

        for scene_index in range(0, root_item.rowCount()):
            scene_item : SceneItem = root_item.child(scene_index, 0)

            for batch_index in range (0, scene_item.rowCount()):
                batch_item : BatchItem = scene_item.child(batch_index, 0)

                if not batch_item or not isinstance(batch_item, BatchItem):
                    logging.error(f"Scene Item {scene_index} has invalid child {batch_index}: {type(batch_item).__name__}")
                    break
                
                if (scene_item.number, batch_item.number) in batch_numbers:
                    lines = batch_item.translated if self.show_translated else batch_item.originals
                    visible_lines = [ (scene_item.number, batch_item.number, line) for line in lines.keys() ]
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

        line_index = index.row()
        if line_index < len(self.visible):
            scene, batch, line = self.visible[line_index]

            item = self.viewmodel.GetLineItem(line, get_translated=self.show_translated)
        else:
            item = LineItem()

        if role == Qt.ItemDataRole.UserRole:
            return item

        if role == Qt.ItemDataRole.DisplayRole:
            return LineItemView(item)
        
        if role == Qt.ItemDataRole.SizeHintRole:
            return LineItemView(item).sizeHint()

        return None

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() or column != 0 or row < 0 or row >= self.rowCount():
            return QModelIndex()
        
        scene_number, batch_number, line_number = self.visible[row]
        batches : list[BatchItem] = self.viewmodel.model[scene_number].batches
        lines = batches[batch_number].translated if self.show_translated else batches[batch_number].originals
        line : LineItem = lines [line_number]
        return self.createIndex(row, column, line)

    def parent(self, index):
        return QModelIndex()

    def _update_visible_batches(self):
        if self.selected_batch_numbers:
            self.ShowSelectedBatches(self.selected_batch_numbers)
        else:
            self.ShowSelection(ProjectSelection())

    def _reset_visible_batches(self):
        self.ShowSelection(ProjectSelection())


