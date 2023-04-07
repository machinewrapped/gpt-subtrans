import logging
import dotenv

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter
)

from GUI.CommandQueue import CommandQueue
from GUI.FileCommands import LoadSubtitleFile
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectToolbar import ProjectToolbar
from GUI.Widgets.LogWindow import LogWindow
from GUI.Widgets.ModelView import ModelView


# Load environment variables from .env file
dotenv.load_dotenv()

class MainWindow(QMainWindow):
    def __init__(self, parent=None, options=None, filepath=None):
        super().__init__(parent)

        self.setWindowTitle("GUI-Subtrans")
        self.setGeometry(100, 100, 1600, 900)

        # Create the project data model
        self.datamodel = ProjectDataModel(options)

        # Create the command queue
        self.command_queue = CommandQueue(datamodel=self.datamodel)
        self.command_queue.commandExecuted.connect(self._on_command_complete)

        # Create the main widget
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # Create the toolbar
        self.toolbar = ProjectToolbar(main_widget, main_window=self, command_queue=self.command_queue)
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
            self.command_queue.AddCommand(LoadSubtitleFile(filepath))

        self.statusBar().showMessage("Ready.")

    def closeEvent(self, e):
        if self.command_queue:
            self.command_queue.Stop()

        if self.datamodel.project:
            self.datamodel.project.UpdateProjectFile()

        super().closeEvent(e)

    def _on_command_complete(self, command, success):
        if success:
            self.statusBar().showMessage(f"{type(command).__name__} was successful.")

            if not self.datamodel or not self.datamodel.project:
                return

            if self.model_viewer:
                self.model_viewer.SetProject(self.datamodel.project)

                # TODO: add model updates to the datamodel rather than rebuilding it 
                viewmodel = self.datamodel.CreateViewModel()
                self.model_viewer.Populate(viewmodel)

        else:
            self.statusBar().showMessage(f"{type(command).__name__} failed.")

    def _on_options_changed(self, options: dict):
        if options and self.datamodel.project:
            self.datamodel.project.UpdateProjectOptions(options)