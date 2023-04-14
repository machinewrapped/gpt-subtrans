import logging
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import Qt, Signal
from GUI.ProjectSelection import ProjectSelection
from GUI.ProjectViewModel import ProjectViewModel
from GUI.Widgets.SelectionView import SelectionView

from GUI.Widgets.SubtitleView import SubtitleView

class ContentView(QWidget):
    onTranslateSelection = Signal()
    onMergeSelection = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.subtitle_view = SubtitleView(show_translated = False, parent=self)
        self.translation_view = SubtitleView(show_translated = True, parent=self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.subtitle_view)
        splitter.addWidget(self.translation_view)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.selection_view = SelectionView()
        self.selection_view.onTranslateSelection.connect(self.onTranslateSelection)
        self.selection_view.onMergeSelection.connect(self.onMergeSelection)

        # connect the selection handlers
        self.subtitle_view.subtitlesSelected.connect(self._subtitles_selected)
        self.translation_view.subtitlesSelected.connect(self._translations_selected)

#        # connect the scrollbars
        self.subtitle_view.SynchroniseScrollbar(self.translation_view.verticalScrollBar())
        self.translation_view.SynchroniseScrollbar(self.subtitle_view.verticalScrollBar())

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.addWidget(self.selection_view)
        self.setLayout(layout)

    def ShowSelection(self, selection : ProjectSelection):
        self.subtitle_view.ShowSelectedBatches(selection)
        self.translation_view.ShowSelectedBatches(selection)
        self.selection_view.ShowSelection(selection)

    def Populate(self, viewmodel):
        self.subtitle_view.SetViewModel(viewmodel)
        self.translation_view.SetViewModel(viewmodel)
        self.selection_view.ShowSelection(ProjectSelection())

    def Clear(self):
        viewmodel = ProjectViewModel()
        self.subtitle_view.SetViewModel(viewmodel)
        self.translation_view.SetViewModel(viewmodel)
        self.selection_view.ShowSelection(ProjectSelection())

    def _subtitles_selected(self, subtitles):
        debug_output = '\n'.join([str(x) for x in subtitles])
        logging.debug(f"Selected subtitles: {debug_output}")
        matching_translations = [ subtitle.translated_index for subtitle in subtitles if subtitle.translated_index ]
        if matching_translations:
            self.translation_view.SelectSubtitles(matching_translations)

    def _translations_selected(self, translations):
        debug_output = '\n'.join([str(x) for x in translations])
        logging.debug(f"Selected translations: {debug_output}")
        translated_indexes = [ item.index for item in translations if item.index ]
        self.subtitle_view.SelectSubtitles(translated_indexes)
