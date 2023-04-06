from PySide6.QtWidgets import QWidget, QSplitter, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from GUI.Widgets.ScenesView import ScenesView
from GUI.Widgets.ContentView import ContentView
from GUI.Widgets.ProjectOptions import ProjectOptions

class ModelView(QWidget):
    optionsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Scenes & Batches Panel
        self.scenesView = ScenesView(self)

        # Main Content Area
        self.contentView = ContentView(self)

        # Project Options
        self.projectOptions = ProjectOptions()
        self.projectOptions.hide()
        self.projectOptions.optionsChanged.connect(self.optionsChanged)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.projectOptions)
        splitter.addWidget(self.scenesView)
        splitter.addWidget(self.contentView)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 3)

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

    def set_project(self, project):
        if not project or not project.options:
            self.projectOptions.clear()
            self.projectOptions.hide()
        else:
            self.projectOptions.populate(project.options.options)
            self.projectOptions.show()

    def toggle_project_options(self):
        if self.projectOptions.isVisible():
            self.optionsChanged.emit(self.projectOptions.get_options())
            self.projectOptions.hide()
        else:
            self.projectOptions.show()

    def show_subtitles(self, subtitles, translations, contexts):
        if subtitles:
            self.contentView.show_subtitles(subtitles)
        
        if translations:
            self.contentView.show_translations(translations)

        if contexts:
            self.contentView.show_contexts(contexts)