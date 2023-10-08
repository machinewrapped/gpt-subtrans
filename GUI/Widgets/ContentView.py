import logging
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget, QSizePolicy, QDialog
from PySide6.QtCore import Qt, QMutexLocker, Signal, Slot
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

        self.subtitle_view = SubtitleView(show_translated = False, parent=self)
        self.translation_view = SubtitleView(show_translated = True, parent=self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.subtitle_view)
        splitter.addWidget(self.translation_view)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.selection_view = SelectionView()
        self.selection_view.actionRequested.connect(self.actionRequested)

        # connect the selection handlers
        self.subtitle_view.linesSelected.connect(self._originals_selected)
        self.translation_view.linesSelected.connect(self._translations_selected)

#        # connect the scrollbars
        self.subtitle_view.SynchroniseScrollbar(self.translation_view.verticalScrollBar())
        self.translation_view.SynchroniseScrollbar(self.subtitle_view.verticalScrollBar())

        # connect the editors
        self.subtitle_view.editLine.connect(self._edit_line)
        self.translation_view.editLine.connect(self._edit_line)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.addWidget(self.selection_view)
        self.setLayout(layout)

    def ShowSelection(self, selection : ProjectSelection):
        self.subtitle_view.ShowSelection(selection)
        self.translation_view.ShowSelection(selection)
        self.selection_view.ShowSelection(selection)

    def Populate(self, viewmodel : ProjectViewModel):
        self.viewmodel = viewmodel
        self.viewmodel.updatesPending.connect(self._update_view_model)
        self.subtitle_view.SetViewModel(viewmodel)
        self.translation_view.SetViewModel(viewmodel)
        self.selection_view.ShowSelection(ProjectSelection())

    def Clear(self):
        self.viewmodel = ProjectViewModel()
        self.subtitle_view.SetViewModel(self.viewmodel)
        self.translation_view.SetViewModel(self.viewmodel)
        self.selection_view.ShowSelection(ProjectSelection())

    def GetSelectedLines(self):
        selected_originals = self.subtitle_view.GetSelectedLines()
        selected_translations = self.translation_view.GetSelectedLines()
        return selected_originals, selected_translations
    
    def ClearSelectedLines(self):
        self.subtitle_view.ClearSelectedLines()
        self.translation_view.ClearSelectedLines()

    def _originals_selected(self, originals):
        line_numbers = [ item.number for item in originals if item.number ]
        if line_numbers:
            self.translation_view.SelectSubtitles(line_numbers)
            
        self.onSelection.emit()

    def _translations_selected(self, translations):
        # line_numbers = [ item.number for item in translations if item.number ]
        # if line_numbers:
        #     self.subtitle_view.SelectSubtitles(line_numbers)
        pass

    def _edit_line(self, item : LineItem):
        if not isinstance(item, LineItem):
            raise Exception("Double-clicked something unexpected")
        
        if not item.number:
            logging.error("Can't identify the line number")
        
        if item.is_translation:
            translated : LineItem = item
            original : LineItem = self.viewmodel.GetLineItem(item.number, get_translated=False)
        else:
            original : LineItem = item
            translated : LineItem = self.viewmodel.GetLineItem(item.number, get_translated=True)

        dialog = EditSubtitleDialog(original, translated)

        if dialog.exec() == QDialog.Accepted:
            if dialog.model:
                original_text = dialog.model.get('original_text')
                translated_text = dialog.model.get('translated_text')

                self.actionRequested.emit('Update Line', (item.number, original_text, translated_text,))

    @Slot()
    def _update_view_model(self):
        if self.viewmodel:
            self.viewmodel.ProcessUpdates()
