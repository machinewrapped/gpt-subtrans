from PySide6.QtWidgets import QToolBar, QFileDialog, QApplication
from PySide6.QtGui import QAction

from GUI.CommandQueue import CommandQueue
from GUI.FileCommands import *
from GUI.Widgets.ModelView import ModelView

class ProjectToolbar(QToolBar):
    command_queue: CommandQueue

    def __init__(self,  parent=None, main_window=None, command_queue=None):
        super().__init__(parent)
        self.main_window = main_window
        self.command_queue = command_queue

        self.setMovable(False)

        # Add the file commands to the toolbar
        load_subtitle_action = QAction("Load Subtitles", self)
        load_subtitle_action.triggered.connect(self._load_subtitle_file)
        self.addAction(load_subtitle_action)

        # save_project_action = QAction("Save Project", self)
        # save_project_action.triggered.connect(self.save_project_file)
        # self.addAction(save_project_action)

        project_options_action = QAction("Project Options", self)
        project_options_action.triggered.connect(self._toggle_project_options)
        self.addAction(project_options_action)

        # save_subtitle_action = QAction("Save Subtitle File", self)
        # save_subtitle_action.triggered.connect(self.save_subtitle_file)
        # self.addAction(save_subtitle_action)

        # save_translation_action = QAction("Save Translation File", self)
        # save_translation_action.triggered.connect(self.save_translation_file)
        # self.addAction(save_translation_action)

        # undo_action = QAction("Undo", self)
        # undo_action.triggered.connect(lambda: command_queue.undo_last_command())
        # self.addAction(undo_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        self.addAction(quit_action)

    def _quit(self):
        QApplication.instance().quit()

    def _load_subtitle_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Subtitle files (*.srt;*.subtrans);;All Files (*)")

        if filepath:
            command = LoadSubtitleFile(filepath)
            self.command_queue.AddCommand(command)

    def _toggle_project_options(self):
        model_viewer: ModelView = self.main_window.model_viewer
        model_viewer.ToggleProjectOptions()
