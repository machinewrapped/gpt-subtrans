import logging
import dotenv

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter
)
from GUI.Command import Command

from GUI.CommandQueue import CommandQueue
from GUI.FileCommands import LoadSubtitleFile
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectToolbar import ProjectToolbar
from GUI.Widgets.LogWindow import LogWindow
from GUI.Widgets.ModelView import ModelView
from PySubtitleGPT import SubtitleProject


# Load environment variables from .env file
dotenv.load_dotenv()

class MainWindow(QMainWindow):
    datamodel : ProjectDataModel = None
    project : SubtitleProject = None

    def __init__(self, parent=None, options=None, filepath=None):
        super().__init__(parent)

        self.setWindowTitle("GUI-Subtrans")
        self.setGeometry(100, 100, 1600, 900)

        # Create the project data model
        self.datamodel = ProjectDataModel(options)

        # Create the command queue
        self.command_queue = CommandQueue()
        self.command_queue.commandExecuted.connect(self._on_command_complete)

        # Create the main widget
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # Create the toolbar
        self.toolbar = ProjectToolbar(main_widget, main_window=self)
        main_layout.addWidget(self.toolbar)

        # Create a splitter widget to divide the remaining vertical space between the project viewer and log window
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)

        self.model_viewer = ModelView(splitter)
        self.model_viewer.optionsChanged.connect(self._on_options_changed)
        splitter.addWidget(self.model_viewer)

        # Create the log window widget and add it to the splitter
        log_window_widget = LogWindow(splitter)
        splitter.addWidget(log_window_widget)

        # Set the sizes of the splitter panes
        splitter.setSizes([int(self.height() * 0.8), int(self.height() * 0.2)])

        # Load file if we were opened with one
        if filepath:
            self.QueueCommand(LoadSubtitleFile(filepath))

        self.statusBar().showMessage("Ready.")

    def QueueCommand(self, command: Command):
        """
        Add a command to the command queue and set the datamodel
        """
        self.command_queue.AddCommand(command, self.datamodel)

    def closeEvent(self, e):
        if self.command_queue:
            self.command_queue.Stop()

        if self.project:
            self.project.UpdateProjectFile()

        super().closeEvent(e)

    def _on_command_complete(self, command : Command, success):
        if success:
            self.statusBar().showMessage(f"{type(command).__name__} was successful.")

            if isinstance(command, LoadSubtitleFile):
                self.project = command.project

            self.datamodel = command.datamodel
            if not self.datamodel:
                return

            if self.model_viewer:
                # TODO: add model updates to the viewmodel rather than rebuilding it 
                self.datamodel.CreateViewModel()
                self.model_viewer.SetViewModel(self.datamodel.viewmodel)
                self.model_viewer.SetProjectOptions(self.datamodel.options)

        else:
            self.statusBar().showMessage(f"{type(command).__name__} failed.")

    def _on_options_changed(self, options: dict):
        if options and self.project:
            self.project.UpdateProjectOptions(options)