from PySide6.QtWidgets import QListView, QAbstractItemView
from PySide6.QtCore import Qt, QItemSelectionModel, QItemSelection, Signal, QSignalBlocker
from GUI.ProjectSelection import ProjectSelection, SelectionLine

from GUI.ProjectViewModel import ProjectViewModel, LineItem
from GUI.Widgets.SubtitleItemDelegate import SubtitleItemDelegate
from GUI.Widgets.SubtitleListModel import SubtitleListModel

class SubtitleView(QListView):
    linesSelected = Signal(list)

    synchronise_scrolling = True    # TODO: Make this an option on the toolbar

    def __init__(self, show_translated, parent=None):
        super().__init__(parent)

        self.show_translated = show_translated

        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)

        item_delegate = SubtitleItemDelegate()
        self.setItemDelegate(item_delegate)

    def SetViewModel(self, viewmodel : ProjectViewModel):
        model = SubtitleListModel(self.show_translated, viewmodel)
        self.setModel(model)

    def ShowSelection(self, selection : ProjectSelection):
        self.model().ShowSelection(selection)

    def GetSelectedLines(self):
        model = self.model()
        selected_indexes = self.selectedIndexes()
        selected_items = [ model.data(index, Qt.ItemDataRole.UserRole) for index in selected_indexes ]
        selected_lines = [ SelectionLine(item.scene, item.batch, item.number, True) for item in selected_items ]
        return selected_lines
    
    def ClearSelectedLines(self):
        selection_model = self.selectionModel()
        selection_model.clearSelection()

    def SelectSubtitles(self, line_numbers):
        """
        Select lines with number in the given list
        """
        model = self.model()
        if not model:
            return

        selection_model = self.selectionModel()
        selection_flags = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
        selected_indexes = []

        with QSignalBlocker(selection_model):
            for row in range(model.rowCount()):
                item_index = model.index(row, 0)
                row_item : LineItem = model.data(item_index, Qt.ItemDataRole.UserRole)
                if isinstance(row_item, LineItem):
                    if row_item.number and row_item.number in line_numbers:
                        selection_model.select(item_index, selection_flags)
                        selected_indexes.append(item_index)

            for index in self.selectedIndexes():
                if index not in selected_indexes:
                    selection_model.select(index, QItemSelectionModel.Deselect)

        # Update the viewport to refresh the list view
        self.viewport().update()

    def SelectAll(self):
        """
        Select all lines in the list view
        """
        model = self.model()
        if not model:
            return

        selection_model = self.selectionModel()
        selection_flags = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows

        with QSignalBlocker(selection_model):
            # Create a selection range that covers all the items in the model
            first_index = model.index(0, 0)
            last_index = model.index(model.rowCount() - 1, 0)
            selection_range = QItemSelection(first_index, last_index)

            # Select the range and update the selection model
            selection_model.select(selection_range, selection_flags)
            self.setSelectionModel(selection_model)

        # Update the viewport to refresh the list view
        self.viewport().update()

    def SynchroniseScrollbar(self, scrollbar):
        scrollbar.valueChanged.connect(self._partner_scrolled)

    def _partner_scrolled(self, value):
        if self.synchronise_scrolling:
            self.verticalScrollBar().setValue(value)

    def selectionChanged(self, selected, deselected):
        model : SubtitleListModel = self.model()

        selected_indexes = self.selectedIndexes()
        if selected_indexes:
            selected_items = [ model.data(index, role=Qt.ItemDataRole.UserRole) for index in selected_indexes]
            selected_lines = [item for item in selected_items if isinstance(item, LineItem)]

            self.linesSelected.emit(selected_lines)

    def keyPressEvent(self, event):
        """
        Handle keyboard events for the list view
        """
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_A:
            # Ctrl+A pressed, select all items if the list view has focus
            if self.hasFocus():
                self.SelectAll()
        else:
            # Call the base class method to handle other key events
            super().keyPressEvent(event)