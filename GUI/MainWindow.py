import os
import logging
import dotenv
import darkdetect

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QDialog
)
from GUI.Command import Command

from GUI.CommandQueue import CommandQueue
from GUI.FileCommands import LoadSubtitleFile
from GUI.FirstRunOptions import FirstRunOptions
from GUI.MainToolbar import MainToolbar
from GUI.ProjectActions import ProjectActions
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Widgets.LogWindow import LogWindow
from GUI.Widgets.ModelView import ModelView
from PySubtitleGPT.Helpers import GetResourcePath
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleProject import SubtitleProject
from PySubtitleGPT.version import __version__

# Load environment variables from .env file
dotenv.load_dotenv()

def LoadStylesheet(name):
    if not name or name == "default":
        name = "subtrans-dark" if darkdetect.isDark() else "subtrans"

    filepath = GetResourcePath(os.path.join("theme", f"{name}.qss"))
    logging.info(f"Loading stylesheet from {filepath}")
    with open(filepath, 'r') as file:
        stylesheet = file.read()
    QApplication.instance().setStyleSheet(stylesheet)
    return stylesheet

class MainWindow(QMainWindow):
    datamodel : ProjectDataModel = None
    project : SubtitleProject = None

    def __init__(self, parent=None, options : Options = None, filepath : str = None):
        super().__init__(parent)

        self.setWindowTitle("GUI-Subtrans")
        self.setGeometry(100, 100, 1600, 900)

        if not options:
            options = Options()
            options.Load()

        theme = options.get('theme', 'default')
        LoadStylesheet(theme)

        # Create the project data model
        self.datamodel = ProjectDataModel(options=options)

        # Create the command queue
        self.command_queue = CommandQueue(self)
        self.command_queue.SetMaxThreadCount(options.get('max_threads', 1))
        self.command_queue.commandExecuted.connect(self._on_command_complete)

        # Create centralised action handler
        self.action_handler = ProjectActions(mainwindow=self)
        self.action_handler.issueCommand.connect(self.QueueCommand)

        # Create the main widget
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # Create the toolbar
        self.toolbar = MainToolbar(self.action_handler)
        main_layout.addWidget(self.toolbar)

        # Create a splitter widget to divide the remaining vertical space between the project viewer and log window
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)

        self.model_viewer = ModelView(splitter)
        self.model_viewer.optionsChanged.connect(self._on_options_changed)
        self.model_viewer.actionRequested.connect(self._on_action_requested)
        splitter.addWidget(self.model_viewer)

        # Create the log window widget and add it to the splitter
        log_window_widget = LogWindow(splitter)
        splitter.addWidget(log_window_widget)

        # Set the sizes of the splitter panes
        splitter.setSizes([int(self.height() * 0.8), int(self.height() * 0.2)])

        if not options.api_key() or options.get('firstrun'):
            # Make sure we have an API key
            self._first_run(options)
        elif filepath:
            # Load file if we were opened with one
            self.QueueCommand(LoadSubtitleFile(filepath))

        logging.info(f"GPT-Subtrans v{__version__}")

        self.statusBar().showMessage("Ready.")

    def QueueCommand(self, command : Command):
        """
        Add a command to the command queue and set the datamodel
        """
        self.command_queue.AddCommand(command, self.datamodel)

    def closeEvent(self, e):
        if self.command_queue:
            self.command_queue.Stop()

        if self.project and self.project.subtitles:
            self.project.UpdateProjectFile()

        super().closeEvent(e)

    def _on_action_requested(self, action_name, params):
        if not self.datamodel:
            raise Exception(f"Cannot perform {action_name} without a data model")

        self.statusBar().showMessage(f"Executing {action_name}")

        try:
            self.datamodel.PerformModelAction(action_name, params)

        except Exception as e:
            logging.error(f"Error in {action_name}: {str(e)}")

    def _on_command_complete(self, command : Command, success):
        if success:
            if self.command_queue.queue_size:
                if self.command_queue.queue_size == 1:
                    self.statusBar().showMessage(f"{type(command).__name__} was successful. One command left in queue.")
                else:
                    self.statusBar().showMessage(f"{type(command).__name__} was successful. {self.command_queue.queue_size} commands in queue.")
            else:
                self.statusBar().showMessage(f"{type(command).__name__} was successful.")

            if isinstance(command, LoadSubtitleFile):
                self.project = command.project

            if command.datamodel_update:
                self.datamodel.UpdateViewModel(command.datamodel_update)
            elif command.datamodel:
                # Shouldn't  need to do a full model rebuild often? 
                self.datamodel = command.datamodel
                self.model_viewer.SetDataModel(self.datamodel)
                self.model_viewer.show()
            else:
                self.model_viewer.hide()


        else:
            self.statusBar().showMessage(f"{type(command).__name__} failed.")

    def _on_options_changed(self, options: dict):
        if options and self.project:
            self.project.UpdateProjectOptions(options)

    def _first_run(self, options: Options):
        settings = options.GetSettings()
        result = FirstRunOptions(settings, self).exec()

        if result == QDialog.Accepted:
            logging.info("First run options set")
            options.update(settings)
            options.add('firstrun', False)
            options.Save()
            LoadStylesheet(options.get('theme'))
