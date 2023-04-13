from PySide6.QtWidgets import QListView, QAbstractItemView
from PySide6.QtCore import Qt, QItemSelectionModel, QItemSelection, Signal, QSignalBlocker

from GUI.ProjectViewModel import SubtitleItem
from GUI.Widgets.SubtitleItemDelegate import SubtitleItemDelegate
from GUI.Widgets.SubtitleListModel import SubtitleListModel

class SubtitleView(QListView):
    subtitlesSelected = Signal(list)

    synchronise_scrolling = True    # TODO: Make this an option on the toolbar

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)

        subtitle_delegate = SubtitleItemDelegate()
        self.setItemDelegate(subtitle_delegate)

    def ShowSubtitles(self, subtitles):
        subtitle_items = [ item if isinstance(item, SubtitleItem) else SubtitleItem(item['index'], item) for item in subtitles ]
        model = SubtitleListModel(subtitle_items)
        self.setModel(model)

    def SelectSubtitles(self, indexes):
        """
        Select subtitles with index in the given list
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
                row_item : SubtitleItem = model.data(item_index, Qt.ItemDataRole.UserRole)
                if isinstance(row_item, SubtitleItem):
                    if row_item.translated_index and row_item.translated_index in indexes:
                        selection_model.select(item_index, selection_flags)
                        selected_indexes.append(item_index)

            for index in self.selectedIndexes():
                if index not in selected_indexes:
                    selection_model.select(index, QItemSelectionModel.Deselect)

        # Update the viewport to refresh the list view
        self.viewport().update()

    def SelectAll(self):
        """
        Select all subtitles in the list view
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
            selected_subtitles = [item for item in selected_items if isinstance(item, SubtitleItem)]

            self.subtitlesSelected.emit(selected_subtitles)

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