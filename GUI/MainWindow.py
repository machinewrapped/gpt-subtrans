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
from GUI.FileCommands import LoadProjectFile
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectToolbar import ProjectToolbar
from GUI.Widgets.LogWindow import LogWindow
from GUI.Widgets.ModelView import ModelView


# Load environment variables from .env file
dotenv.load_dotenv()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the window title
        self.setWindowTitle("GUI-Subtrans")

        # Set the window size
        self.setGeometry(100, 100, 1600, 900)

        # Create the project data model
        self.datamodel = ProjectDataModel()

        # Create the command queue
        self.command_queue = CommandQueue(datamodel=self.datamodel)
        self.command_queue.command_executed.connect(self.on_command_complete)

        # Create the main widget
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # Create the toolbar
        self.toolbar = ProjectToolbar(main_widget, command_queue=self.command_queue)
        main_layout.addWidget(self.toolbar)

        # Create a splitter widget to divide the remaining vertical space between the project viewer and log window
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)

        self.model_viewer = ModelView(splitter)
        splitter.addWidget(self.model_viewer)

        # Create the log window widget and add it to the splitter
        log_window_widget = LogWindow(splitter)
        splitter.addWidget(log_window_widget)

        # Set the sizes of the splitter panes
        splitter.setSizes([int(self.height() * 0.8), int(self.height() * 0.2)])

        # Set up the status bar
        self.statusBar().showMessage("Ready.")

        # TEMP
        self.command_queue.add_command(LoadProjectFile('C:/Development/Projects/GPT/gpt-subtrans/A Hero Never Dies (1998) [FR.1080p].fr.subtrans'))

    def on_command_complete(self, command, success):
        if success:
            self.statusBar().showMessage(f"{type(command).__name__} was successful.")

            if not self.datamodel or not self.datamodel.project:
                return

            if self.model_viewer:
                viewmodel = self.datamodel.CreateViewModel()
                self.model_viewer.populate(viewmodel)

        else:
            self.statusBar().showMessage(f"{type(command).__name__} failed.")

