from PySide6.QtWidgets import QWidget, QSplitter, QHBoxLayout
from PySide6.QtCore import Qt, Signal

from GUI.ProjectSelection import ProjectSelection
from GUI.ProjectToolbar import ProjectToolbar

from GUI.Widgets.ScenesView import ScenesView
from GUI.Widgets.ContentView import ContentView
from GUI.Widgets.ProjectOptions import ProjectOptions

class ModelView(QWidget):
    optionsChanged = Signal(dict)
    actionRequested = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._toolbar = ProjectToolbar(self)
        self._toolbar.toggleOptions.connect(self.ToggleProjectOptions)
        self._toolbar.setVisible(False)
        layout.addWidget(self._toolbar)

        # Scenes & Batches Panel
        self.scenes_view = ScenesView(self)

        # Main Content Area
        self.content_view = ContentView(self)

        # Project Options
        self.project_options = ProjectOptions()
        self.project_options.hide()
        self.project_options.optionsChanged.connect(self.optionsChanged)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.project_options)
        splitter.addWidget(self.scenes_view)
        splitter.addWidget(self.content_view)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 3)

        layout.addWidget(splitter)
        self.setLayout(layout)

        self.scenes_view.onSelection.connect(self._items_selected)
        self.content_view.onSelection.connect(self._lines_selected)

        self.content_view.actionRequested.connect(self.actionRequested)

        self.scenes_view.onBatchEdited.connect(self._on_batch_edited)
        self.scenes_view.onSceneEdited.connect(self._on_scene_edited)

    def SetDataModel(self, datamodel):
        self.SetViewModel(datamodel.viewmodel)
        self.SetProjectOptions(datamodel.options)

    def SetViewModel(self, viewmodel):
        self.content_view.Clear()

        if viewmodel is None:
            self.scenes_view.Clear()
        else:
            self.scenes_view.Populate(viewmodel)
            self.content_view.Populate(viewmodel)

    def SetProjectOptions(self, options):
        self.project_options.Clear()
        if not options:
            self.project_options.hide()
            self._toolbar.hide()
        else:
            self.project_options.Populate(options)

            self._toolbar.show()
            self._toolbar.show_options = not options.get('movie_name', None)
            if self._toolbar.show_options:
                self.project_options.show()

    def ToggleProjectOptions(self, show = None):
        if self.project_options.isVisible() and not show:
            self.CloseProjectOptions()
        else:
            self.project_options.show()

    def CloseProjectOptions(self):
        if self.project_options.isVisible():
            self.optionsChanged.emit(self.project_options.GetOptions())
            self.project_options.hide()

    def GetSelection(self) -> ProjectSelection:
        selection = ProjectSelection()
        model = self.scenes_view.model()

        selected_indexes = self.scenes_view.selectionModel().selectedIndexes()
        for index in selected_indexes:
            selection.AppendItem(model, index)

        selected_lines, selected_translations = self.content_view.GetSelectedLines()
        if selected_lines or selected_translations:
            selection.AddSelectedLines(selected_lines, selected_translations)

        return selection

    def _items_selected(self):
        self.content_view.ClearSelectedLines()
        selection : ProjectSelection = self.GetSelection()
        self.content_view.ShowSelection(selection)

    def _lines_selected(self):
        selection : ProjectSelection = self.GetSelection()
        self.content_view.ShowSelection(selection)

    def _on_scene_edited(self, scene_number, scene_model):
        update = {
            'summary' : scene_model.get('summary')
        }
        self.actionRequested.emit('Update Scene', (scene_number, update,))

    def _on_batch_edited(self, scene, batch_number, batch_model):
        update = {
            'summary' : batch_model.get('summary')
        }
        self.actionRequested.emit('Update Batch', (scene, batch_number, update,))

