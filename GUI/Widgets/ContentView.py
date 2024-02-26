import logging
from PySide6.QtWidgets import QVBoxLayout, QWidget, QDialog
from PySide6.QtCore import Signal, Slot
from GUI.ProjectSelection import ProjectSelection
from GUI.ProjectViewModel import LineItem, ProjectViewModel
from GUI.Widgets.Editors import EditSubtitleDialog
from GUI.Widgets.SelectionView import SelectionView

from GUI.Widgets.SubtitleView import SubtitleView

class ContentView(QWidget):
    onSelection = Signal()
    actionRequested = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.viewmodel = None

        self.subtitle_view = SubtitleView(parent=self)

        self.selection_view = SelectionView()
        self.selection_view.actionRequested.connect(self.actionRequested)

        # connect the selection handlers
        self.subtitle_view.linesSelected.connect(self._lines_selected)

        # connect the editors
        self.subtitle_view.editLine.connect(self._edit_line)

        layout = QVBoxLayout()
        layout.addWidget(self.subtitle_view)
        layout.addWidget(self.selection_view)
        self.setLayout(layout)

    def ShowSelection(self, selection : ProjectSelection):
        if selection.AnyScenes() or selection.AnyBatches():
            self.subtitle_view.ShowSelection(selection)
        self.selection_view.ShowSelection(selection)

    def Populate(self, viewmodel : ProjectViewModel):
        self.viewmodel = viewmodel
        self.viewmodel.updatesPending.connect(self._update_view_model)
        self.subtitle_view.SetViewModel(viewmodel)
        self.selection_view.ShowSelection(ProjectSelection())

    def Clear(self):
        self.viewmodel = ProjectViewModel()
        self.subtitle_view.SetViewModel(self.viewmodel)
        self.selection_view.ShowSelection(ProjectSelection())

    def GetSelectedLines(self):
        return self.subtitle_view.GetSelectedLines()
    
    def ClearSelectedLines(self):
        self.subtitle_view.ClearSelectedLines()

    def _lines_selected(self, originals):
        self.onSelection.emit()

    def _edit_line(self, item : LineItem):
        if not isinstance(item, LineItem):
            raise Exception("Double-clicked something unexpected")
        
        if not item.number:
            logging.error("Can't identify the line number")
        
        dialog = EditSubtitleDialog(item)

        if dialog.exec() == QDialog.Accepted:
            if dialog.model:
                original_text = dialog.model.get('original')
                translated_text = dialog.model.get('translated')

                self.actionRequested.emit('Update Line', (item.number, original_text, translated_text,))

    @Slot()
    def _update_view_model(self):
        if self.viewmodel:
            self.viewmodel.ProcessUpdates()
