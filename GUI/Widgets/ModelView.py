from PySide6.QtWidgets import QWidget, QSplitter, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from GUI.ProjectToolbar import ProjectToolbar

from GUI.Widgets.ScenesView import ScenesView
from GUI.Widgets.ContentView import ContentView
from GUI.Widgets.ProjectOptions import ProjectOptions

class ModelView(QWidget):
    optionsChanged = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._toolbar = ProjectToolbar(self)
        self._toolbar.toggleOptions.connect(self.ToggleProjectOptions)
        self._toolbar.setVisible(False)
        layout.addWidget(self._toolbar)

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

        layout.addWidget(splitter)
        self.setLayout(layout)

        self.scenesView.selectedLines.connect(self.ShowSubtitles)

    def SetViewModel(self, viewmodel):
        self.contentView.Clear()

        if viewmodel is None:
            self.scenesView.Clear()
        else:
            self.scenesView.Populate(viewmodel)

    def SetProjectOptions(self, options):
        self.projectOptions.Clear()
        if not options:
            self.projectOptions.hide()
            self._toolbar.hide()
        else:
            self.projectOptions.Populate(options)
            self.projectOptions.show()
            self._toolbar.show()

    def ToggleProjectOptions(self, show = None):
        if self.projectOptions.isVisible() and not show:
            self.optionsChanged.emit(self.projectOptions.GetOptions())
            self.projectOptions.hide()
        else:
            self.projectOptions.show()

    def ShowSubtitles(self, subtitles, translations, contexts):
        if subtitles:
            self.contentView.ShowSubtitles(subtitles)
        
        if translations:
            self.contentView.ShowTranslations(translations)

        if contexts:
            self.contentView.ShowContexts(contexts)

