from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QFileDialog, QApplication, QMainWindow, QStyle

from GUI.FileCommands import *
from GUI.ProjectCommands import MergeBatchesCommand, MergeScenesCommand, TranslateSceneCommand
from GUI.ProjectSelection import ProjectSelection
from GUI.Widgets.ModelView import ModelView

class ProjectActions(QObject):
    issueCommand = Signal(object)

    _actions = {}

    def __init__(self, mainwindow : QMainWindow = None):
        super().__init__()
        self._mainwindow = mainwindow
        self.AddAction('Quit', self._quit, QStyle.StandardPixmap.SP_DialogCloseButton, 'Ctrl+W', 'Exit Program')
        self.AddAction('Load Subtitles', self._load_subtitle_file, QStyle.StandardPixmap.SP_DialogOpenButton)
        self.AddAction('Save Project', self._save_project_file, QStyle.StandardPixmap.SP_DialogSaveButton, 'Ctrl+S', 'Save project')
        self.AddAction('Project Options', self._toggle_project_options, QStyle.StandardPixmap.SP_FileDialogDetailedView, 'Ctrl+/', 'Project Options')

        #TODO: Mixing different concepts of "action" here, is there a better separation?
        ProjectDataModel.RegisterActionHandler('Translate Selection', self._translate_selection)
        ProjectDataModel.RegisterActionHandler('Merge Selection', self._merge_selection)

    def AddAction(self, name, function : callable, icon=None, shortcut=None, tooltip=None):
        action = QAction(name)
        action.triggered.connect(function)

        if icon:
            if isinstance(icon, QStyle.StandardPixmap):
                icon = QApplication.style().standardIcon(icon)
            else:
                icon = QIcon(icon)
            action.setIcon(icon)

        if shortcut:
            action.setShortcut(shortcut)

        if tooltip:
            action.setToolTip(f"{tooltip} ({shortcut})" if shortcut else tooltip)

        self._actions[name] = action


    def GetAction(self, name : str) -> QAction:
        return self._actions[name]

    def GetActionList(self, names : list) -> list[QAction]:
        return [ self.GetAction(name) for name in names ]
    
    def _issue_command(self, command : Command):
        self.issueCommand.emit(command)

    def _quit(self):
        QApplication.instance().quit()

    def _load_subtitle_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self._mainwindow, "Open File", "", "Subtitle files (*.srt;*.subtrans);;All Files (*)")

        if filepath:
            command = LoadSubtitleFile(filepath)
            self._issue_command(command)

    def _save_project_file(self):
        # TODO: Don't ask the main window for the project
        project : SubtitleProject = self._mainwindow.project
        if not project:
            logging.error("Nothing to save!")
            return

        filepath = project.projectfile
        if not filepath or self._is_shift_pressed():
            filepath, _ = QFileDialog.getSaveFileName(self._mainwindow, "Save Project File", filepath, "Subtrans projects (*.subtrans);;All Files (*)")

        if filepath:
            command = SaveProjectFile(filepath, self._mainwindow.project)
            self._issue_command(command)

    def _is_shift_pressed(self):
        return QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier

    def _toggle_project_options(self):
        # TODO: Route GUI actions with signals and events or something
        model_viewer: ModelView = self._mainwindow.model_viewer
        model_viewer.ToggleProjectOptions()

    def _translate_selection(self, datamodel, selection : ProjectSelection):
        if not selection.Any():
            logging.error("Nothing selected to translate")
            return

        logging.info(f"Translate selection of {str(selection)}")

        for scene in selection.scenes.values():
            batch_numbers = [ batch.number for batch in scene.batches.values() if batch.selected ]
            command = TranslateSceneCommand(scene.number, batch_numbers, datamodel)
            self._issue_command(command)

    def _merge_selection(self, datamodel, selection : ProjectSelection):
        if not selection.Any():
            logging.error("Nothing selected to merge")
            return
        
        if not selection.SelectionIsSequential():
            logging.error("Cannot merge non-sequential elements")
            return
        
        if selection.OnlyScenes():
            self._issue_command(MergeScenesCommand(selection.scene_numbers, datamodel))

        elif selection.OnlyBatches():
            scene_number = selection.batch_numbers[0][0]
            batch_numbers = [ batch[1] for batch in selection.batch_numbers ]
            self._issue_command(MergeBatchesCommand(scene_number, batch_numbers, datamodel))

        else:
            logging.error(f"Invalid selection for merge ({str(selection)})")
