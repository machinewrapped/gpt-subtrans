from PySide6.QtWidgets import QSplitter, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from GUI.Widgets.SubtitleView import SubtitleView

class ContentView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.subtitles = SubtitleView(self)
        self.translations = SubtitleView(self)
        metadata_context = QLabel("Metadata & Context Information")

        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.subtitles)
        splitter.addWidget(self.translations)
        layout.addWidget(splitter)
        layout.addWidget(metadata_context)

        self.setLayout(layout)
