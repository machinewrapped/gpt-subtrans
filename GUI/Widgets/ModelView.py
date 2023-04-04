from PySide6.QtWidgets import QWidget, QSplitter, QVBoxLayout
from PySide6.QtCore import Qt
from GUI.Widgets.ContentView import ContentView

from GUI.Widgets.ScenesView import ScenesView

class ModelView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Scenes & Batches Panel
        self.scenesView = ScenesView(self)

        # Main Content Area
        self.contentView = ContentView(self)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.scenesView)
        splitter.addWidget(self.contentView)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self.setLayout(layout)

        self.scenesView.selectedLines.connect(self.show_subtitles)

    def populate(self, viewmodel):
        self.contentView.clear()
        if viewmodel is None:
            self.scenesView.clear()
        else:
            self.scenesView.populate(viewmodel)

    def show_subtitles(self, subtitles, translations, contexts):
        if subtitles:
            self.contentView.show_subtitles(subtitles)
        
        if translations:
            self.contentView.show_translations(translations)

        if contexts:
            self.contentView.show_contexts(contexts)