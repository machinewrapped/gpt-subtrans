import logging
from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtCore import Qt, QItemSelectionModel, Signal
from GUI.ProjectViewModel import BatchItem, SceneItem

from GUI.Widgets.ScenesBatchesModel import ScenesBatchesModel
from GUI.Widgets.ScenesBatchesDelegate import ScenesBatchesDelegate

class ScenesView(QTreeView):
    selectedLines = Signal(list, list, list)

    def __init__(self, parent=None, viewmodel=None):
        super().__init__(parent)

        self.setMinimumWidth(350)
        self.setIndentation(20)
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(True)
        self.setAnimated(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.setItemDelegate(ScenesBatchesDelegate(self))  
        self.Populate(viewmodel)

    def Clear(self):
        self.Populate([])

    def Populate(self, viewmodel):
        self.viewmodel = viewmodel
        self.model = ScenesBatchesModel(self.viewmodel)
        self.setModel(self.model)
        self.selectionModel().selectionChanged.connect(self.item_selected)

    def item_selected(self, selected, deselected):
        model = self.model

        for index in selected.indexes():
            data = model.data(index, role=Qt.ItemDataRole.UserRole)
            if isinstance(data, SceneItem):
                # If a scene is selected, expand the node and select the batches
                self.expand(index)

                scene_item = data
                selection_model = self.selectionModel()
                selection_flags = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows

                for row in range(scene_item.rowCount()):
                    batch_item_index = model.index(row, 0, index)
                    selection_model.select(batch_item_index, selection_flags)

        self.emit_selected_batches()

    def emit_selected_batches(self):
        model = self.model

        selected_indexes = self.selectionModel().selectedIndexes()
        selected_items = [ model.data(index, role=Qt.ItemDataRole.UserRole) for index in selected_indexes]
        selected_batches = [item for item in selected_items if isinstance(item, BatchItem)]

        subtitles = []
        translated = []
        contexts = []
        for batch in selected_batches:
            subtitles.extend(batch.subtitles)
            if batch.translated:
                translated.extend(batch.translated)
            if batch.context:
                contexts.append(batch.context)

        debug_output = '\n'.join([str(x) for x in subtitles])
        logging.debug(f"Selected lines: {debug_output}")

        self.selectedLines.emit(subtitles, translated, contexts)