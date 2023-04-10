import logging
from PySide6.QtWidgets import QSplitter, QLabel, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import Qt
from GUI.ProjectSelection import ProjectSelection
from GUI.Widgets.SelectionView import SelectionView

from GUI.Widgets.SubtitleView import SubtitleView

class ContentView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.subtitle_view = SubtitleView(self)
        self.translation_view = SubtitleView(self)

        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.subtitle_view)
        splitter.addWidget(self.translation_view)
        splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(splitter)

        self.selection_view = SelectionView()
        layout.addWidget(self.selection_view)

        # connect the selection handlers
        self.subtitle_view.subtitlesSelected.connect(self._subtitles_selected)
        self.translation_view.subtitlesSelected.connect(self._translations_selected)

#        # connect the scrollbars
        self.subtitle_view.SynchroniseScrollbar(self.translation_view.verticalScrollBar())
        self.translation_view.SynchroniseScrollbar(self.subtitle_view.verticalScrollBar())

        self.setLayout(layout)

    def ShowSubtitles(self, subtitles):
        self.subtitle_view.ShowSubtitles(subtitles)
    
    def ShowTranslated(self, translations):
        self.translation_view.ShowSubtitles(translations)

    def ShowSelection(self, selection : ProjectSelection):
        self.ShowSubtitles(selection.subtitles)
        self.ShowTranslated(selection.translated)
        self.selection_view.ShowSelection(selection)

    def Clear(self):
        self.subtitle_view.ShowSubtitles([])
        self.translation_view.ShowSubtitles([])
        # self.metadata_context.show_contexts([])

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
