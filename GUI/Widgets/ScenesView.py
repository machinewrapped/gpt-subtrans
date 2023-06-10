import logging
from PySide6.QtWidgets import QTreeView, QAbstractItemView, QDialog
from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex, QItemSelectionModel, QItemSelection, QItemSelectionRange, Signal
from GUI.ProjectViewModel import BatchItem, SceneItem, ViewModelItem
from GUI.Widgets.Editors import EditBatchDialog, EditSceneDialog

from GUI.Widgets.ScenesBatchesModel import ScenesBatchesModel
from GUI.Widgets.ScenesBatchesDelegate import ScenesBatchesDelegate

class ScenesView(QTreeView):
    onSelection = Signal()

    onSceneEdited = Signal(int, object)
    onBatchEdited = Signal(int, int, object)

    def __init__(self, parent=None, viewmodel=None):
        super().__init__(parent)

        self.setMinimumWidth(450)
        self.setIndentation(20)
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(False)
        self.setAnimated(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.doubleClicked.connect(self._on_double_click)

        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(16)  # Per-pixel scrolling doesn't work unless we set a step

        self.setItemDelegate(ScenesBatchesDelegate(self))  
        self.Populate(viewmodel)

    def Clear(self):
        self.Populate([])

    def Populate(self, viewmodel):
        self.viewmodel = viewmodel

        model = ScenesBatchesModel(self.viewmodel)
        self.setModel(model)
        self.selectionModel().selectionChanged.connect(self._item_selected)

    def SelectAll(self):
        model = self.model()
        if not model:
            return

        selection = QItemSelection()
        first_index = model.index(0, 0, QModelIndex())
        last_index = model.index(model.rowCount(QModelIndex()) - 1, 0, QModelIndex())
        selection_range = QItemSelectionRange(first_index, last_index)
        selection.append(selection_range)

        self.selectionModel().select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)
    
    def _item_selected(self, selected, deselected):
        model : QAbstractItemModel = self.model()

        for index in selected.indexes():
            data = model.data(index, role=Qt.ItemDataRole.UserRole)
            if isinstance(data, SceneItem):
                # self._select_batches_in_scene(model, index, data)
                self._deselect_children(model, index, data)
                self.expand(index)
            elif isinstance(data, BatchItem):
                self._deselect_parent(model, index)
                # self._deselect_children(model, index, data)

        self.onSelection.emit()

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

    def keyPressEvent(self, event):
        """
        Handle keyboard events for the tree view
        """
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_A:
            # Ctrl+A pressed, select all items if the list view has focus
            if self.hasFocus():
                self.SelectAll()
        else:
            # Call the base class method to handle other key events
            super().keyPressEvent(event)
    
    def _on_double_click(self, index):
        item: ViewModelItem = index.internalPointer()

        try:
            if isinstance(item, BatchItem):
                if self._edit_batch(item):
                    self.model().dataChanged.emit(index, index)
            elif isinstance(item, SceneItem):
                if self._edit_scene(item):
                    self.model().dataChanged.emit(index, index)
            else:
                logging.error("Not sure what you just double-clicked on")
        except Exception as e:
            logging.error(str(e))

    def _edit_scene(self, item : SceneItem):
        dialog = EditSceneDialog(item, parent = self)

        if dialog.exec() == QDialog.Accepted:
            if dialog.model:
                item.Update(dialog.model)
                self.onSceneEdited.emit(item.number, item.scene_model)
                return True

        return False

    def _edit_batch(self, item : BatchItem):
        dialog = EditBatchDialog(item)

        if dialog.exec() == QDialog.Accepted:
            if dialog.model:
                item.Update(dialog.model)
                self.onBatchEdited.emit(item.scene, item.number, item.batch_model)
                return True

        return False