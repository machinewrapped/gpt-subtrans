from PySide6.QtWidgets import QSplitter, QLabel, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import Qt

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

        metadata_context = QLabel("Metadata & Context Information")
        metadata_context.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addWidget(metadata_context)

#        # connect the scrollbars
        self.subtitle_view.SynchroniseScrollbar(self.translation_view.verticalScrollBar())
        self.translation_view.SynchroniseScrollbar(self.subtitle_view.verticalScrollBar())

        self.setLayout(layout)

    def ShowSubtitles(self, subtitles):
        self.subtitle_view.ShowSubtitles(subtitles)
    
    def ShowTranslations(self, translations):
        self.translation_view.ShowSubtitles(translations)

    def ShowContexts(self, contexts):
        # self.metadata_context.show_contexts(contexts)
        pass

    def Clear(self):
        self.subtitle_view.ShowSubtitles([])
        self.translation_view.ShowSubtitles([])
        # self.metadata_context.show_contexts([])
