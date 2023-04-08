from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QFileDialog, QApplication, QStyle

from GUI.FileCommands import *
from GUI.Widgets.ModelView import ModelView

class ProjectActions(QObject):
    issueCommand = Signal(object)

    _actions = {}

    def __init__(self, mainwindow=None):
        super().__init__()
        self._mainwindow = mainwindow
        self.AddAction('Quit', self._quit, QStyle.StandardPixmap.SP_DialogCloseButton)
        self.AddAction('Load Subtitles', self._load_subtitle_file, QStyle.StandardPixmap.SP_DialogOpenButton)
        self.AddAction('Save Project', self._save_project_file, QStyle.StandardPixmap.SP_DialogSaveButton)
        self.AddAction('Project Options', self._toggle_project_options, QStyle.StandardPixmap.SP_FileDialogDetailedView)

    def AddAction(self, name, function, icon=None):
        action = QAction(name)
        action.triggered.connect(function)

        if icon:
            if isinstance(icon, QStyle.StandardPixmap):
                icon = QApplication.style().standardIcon(icon)
            else:
                icon = QIcon(icon)
            action.setIcon(icon)

        self._actions[name] = action

    def GetAction(self, name : str):
        return self._actions[name]

    def GetActionList(self, names : list):
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
        if not self._mainwindow.project:
            logging.error("Nothing to save!")
            return

        filepath, _ = QFileDialog.getSaveFileName(self._mainwindow, "Save Project File", "", "Subtrans projects (*.subtrans);;All Files (*)")

        if filepath:
            command = SaveProjectFile(filepath, self._mainwindow.project)
            self._issue_command(command)

    def _toggle_project_options(self):
        # TODO: Route GUI actions with signals and events or something
        model_viewer: ModelView = self._mainwindow.model_viewer
        model_viewer.ToggleProjectOptions()