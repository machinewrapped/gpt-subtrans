import logging
from PySide6.QtCore import QAbstractProxyModel, QModelIndex, Qt, QSize
from GUI.ProjectViewModel import BatchItem, ProjectViewModel, SceneItem, LineItem, ViewModelItem
from GUI.ProjectSelection import ProjectSelection
from GUI.Widgets.Widgets import LineItemView

class SubtitleListModel(QAbstractProxyModel):
    def __init__(self, viewmodel=None, parent=None):
        super().__init__(parent)
        self.viewmodel : ProjectViewModel = viewmodel
        self.selected_batch_numbers = []
        self.visible = []
        self.visible_row_map : dict(int, int) = {}
        self.size_map : dict(int, QSize ) = {}

        # Connect signals to update mapping when source model changes
        if self.viewmodel:
            self.setSourceModel(viewmodel)
            viewmodel.layoutChanged.connect(self._update_visible_batches)

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
                    lines = batch_item.lines
                    visible_lines = [ (scene_item.number, batch_item.number, line) for line in lines.keys() ]
                    visible.extend(visible_lines)
        
        self.visible = visible
        self.visible_row_map = { item[2] : row for row, item in enumerate(self.visible) }
        self.layoutChanged.emit()

    def mapFromSource(self, source_index : QModelIndex):
        item : ViewModelItem = self.viewmodel.itemFromIndex(source_index)

        if isinstance(item, LineItem):
            row = self.visible_row_map.get(item.number, None)
            if row is not None:
                return self.index(row, 0, QModelIndex())

        return QModelIndex()

    def mapToSource(self, index : QModelIndex):
        """
        Map an index into the proxy model to the source model
        """
        if not index.isValid():
            return QModelIndex()

        row = index.row()
        if row > len(self.visible):
            logging.debug(f"Tried to map an unknown row to source model: {row}")
            return QModelIndex()

        key = self.visible[row]
        _, _, line = key

        item = self.viewmodel.GetLineItem(line)
        return self.viewmodel.indexFromItem(item)

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0    # Only top-level items in this model

        return len(self.visible)

    def columnCount(self, parent=QModelIndex()):
        return 1

    def parent(self, index):
        return QModelIndex()  # All items are top-level in the proxy model

    def index(self, row, column, parent=QModelIndex()):
        """
        Create a model index for the given model row 
        """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        scene_number, batch_number, line_number = self.visible[row]

        scene_item = self.viewmodel.model.get(scene_number)
        if not scene_item:
            logging.debug(f"Invalid scene number in SubtitleListModel: {scene_number}")
            return QModelIndex()

        batches = scene_item.batches
        if not batch_number in batches.keys():
            logging.debug(f"Invalid batch number in SubtitleListModel ({scene_number},{batch_number})")
            return QModelIndex()

        lines = batches[batch_number].lines

        if line_number not in lines:
            logging.debug(f"Visible subtitles list has invalid line number ({scene_number},{batch_number},{line_number})")
            return QModelIndex()

        line : LineItem = lines[line_number]

        return self.createIndex(row, column, line)

    def data(self, index, role):
        """
        Fetch the data for an index in the proxy model from the source model
        """
        if index.isValid():
            source_index = self.mapToSource(index)
            item = self.viewmodel.itemFromIndex(source_index)
            if not item:
                logging.debug(f"No item in source model found for index {index.row()}, {index.column()}")
        else:
            item = None

        if not item:
            item = LineItem(-1, { 'start' : "0:00:00,000", 'end' : "0:00:00,000",  'text' : "Invalid index" })

        if role == Qt.ItemDataRole.UserRole:
            return item

        if role == Qt.ItemDataRole.DisplayRole:
            return LineItemView(item)
        
        if role == Qt.ItemDataRole.SizeHintRole:
            if not item.height:
                return LineItemView(item).sizeHint()

            if item.height in self.size_map:
                return self.size_map[item.height]

            size = LineItemView(item).sizeHint()
            self.size_map[item.height] = size
            return size

        return None

    def _update_visible_batches(self):
        if self.selected_batch_numbers:
            self.ShowSelectedBatches(self.selected_batch_numbers)
        else:
            self.ShowSelection(ProjectSelection())

    def _reset_visible_batches(self):
        self.ShowSelection(ProjectSelection())


