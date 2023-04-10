import logging
from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtCore import Qt, QItemSelectionModel, Signal
from GUI.ProjectSelection import ProjectSelection
from GUI.ProjectViewModel import BatchItem, SceneItem

from GUI.Widgets.ScenesBatchesModel import ScenesBatchesModel
from GUI.Widgets.ScenesBatchesDelegate import ScenesBatchesDelegate

class ScenesView(QTreeView):
    onSelection = Signal(object)

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
        self.selectionModel().selectionChanged.connect(self._item_selected)

    def _item_selected(self, selected, deselected):
        model = self.model

        for index in selected.indexes():
            data = model.data(index, role=Qt.ItemDataRole.UserRole)
            if isinstance(data, SceneItem):
                # self._select_batches_in_scene(model, index, data)
                self._deselect_children(model, index, data)
                self.expand(index)
            elif isinstance(data, BatchItem):
                self._deselect_parent(model, index)
                # self._deselect_children(model, index, data)

        self._emit_selection()

    def _emit_selection(self):
        model = self.model

        selection = ProjectSelection()

        selected_indexes = self.selectionModel().selectedIndexes()
        for index in selected_indexes:
            self._append_selection(selection, model, index)

        # debug_output = '\n'.join([str(x) for x in subtitles])
        # logging.debug(f"Selected lines: {debug_output}")

        self.onSelection.emit(selection)

    def _select_children(self, model, index, data):
        scene_item = data
        selection_model = self.selectionModel()
        selection_flags = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows

        for row in range(scene_item.rowCount()):
            batch_item_index = model.index(row, 0, index)
            selection_model.select(batch_item_index, selection_flags)

    def _deselect_children(self, model, index, item):
        selection_model = self.selectionModel()
        selection_flags = QItemSelectionModel.SelectionFlag.Deselect | QItemSelectionModel.SelectionFlag.Rows

        for row in range(item.rowCount()):
            batch_item_index = model.index(row, 0, index)
            selection_model.select(batch_item_index, selection_flags)

    def _deselect_parent(self, model, index):
        selection_model = self.selectionModel()
        selection_flags = QItemSelectionModel.SelectionFlag.Deselect | QItemSelectionModel.SelectionFlag.Rows
        selection_model.select(model.parent(index), selection_flags)

    def _append_selection(self, selection : ProjectSelection, model, index):
        """
        Accumulated selected batches, scenes and subtitles
        """
        item = model.data(index, role=Qt.ItemDataRole.UserRole)
        if isinstance(item, SceneItem):
            selection.scenes.append(item)
            children = [ model.index(i, 0, index) for i in range(model.rowCount(index))]
            batches = [ model.data(child, role=Qt.ItemDataRole.UserRole) for child in children ]
            selection.batches.extend(batches)
            for child in children:
                self._append_selection(selection, model, child)

        elif isinstance(item, BatchItem):
            selection.batches.append(item)
            selection.subtitles.extend(item.subtitles)
            selection.translated.extend(item.translated)
        
        #TODO individual subtitle/translation selection


