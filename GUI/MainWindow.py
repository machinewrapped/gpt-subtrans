import os
import logging
import dotenv
import darkdetect

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QDialog
)
from GUI.AboutDialog import AboutDialog
from GUI.Command import Command
from GUI.CommandQueue import CommandQueue
from GUI.FileCommands import LoadSubtitleFile
from GUI.FirstRunOptions import FirstRunOptions
from GUI.GuiHelpers import GetResourcePath
from GUI.MainToolbar import MainToolbar
from GUI.SettingsDialog import SettingsDialog
from GUI.ProjectActions import NoApiKeyError, ProjectActions
from GUI.ProjectCommands import BatchSubtitlesCommand
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Widgets.LogWindow import LogWindow
from GUI.Widgets.ModelView import ModelView
from GUI.NewProjectSettings import NewProjectSettings
from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.VersionCheck import CheckIfUpdateAvailable, CheckIfUpdateCheckIsRequired
from PySubtitle.version import __version__

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
    def __init__(self, parent=None, options : Options = None, filepath : str = None):
        super().__init__(parent)

        self.setWindowTitle("GUI-Subtrans")
        self.setGeometry(100, 100, 1600, 900)
        self._load_icon("gui-subtrans")

        if not options:
            options = Options()
            options.InitialiseInstructions()
            options.Load()

        self.options = options

        theme = options.get('theme', 'default')
        LoadStylesheet(theme)

        # Create the project data model
        self.datamodel = ProjectDataModel(options=options)

        # Create the command queue
        self.command_queue = CommandQueue(self)
        self.command_queue.SetMaxThreadCount(options.get('max_threads', 1))
        self.command_queue.commandExecuted.connect(self._on_command_complete)
        self.command_queue.commandAdded.connect(self._on_command_added)

        # Create centralised action handler
        self.action_handler = ProjectActions(mainwindow=self, datamodel=self.datamodel)
        self.action_handler.issueCommand.connect(self.QueueCommand)
        self.action_handler.actionError.connect(self._on_error)

        # Create the main widget
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # Create the toolbar
        self.toolbar = MainToolbar(self.action_handler)
        self.toolbar.SetBusyStatus(None, self.command_queue)
        main_layout.addWidget(self.toolbar)

        # Create a splitter widget to divide the remaining vertical space between the project viewer and log window
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)

        self.model_viewer = ModelView(splitter)
        self.model_viewer.optionsChanged.connect(self._on_project_options_changed)
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
            self.QueueCommand(LoadSubtitleFile(filepath, options))

        logging.info(f"GPT-Subtrans {__version__}")

        # Check if there is a more recent version on Github (TODO: make this optional)
        if CheckIfUpdateCheckIsRequired():
            CheckIfUpdateAvailable()

        self.statusBar().showMessage("Ready.")

    def QueueCommand(self, command : Command):
        """
        Add a command to the command queue and set the datamodel
        """
        self.command_queue.AddCommand(command, self.datamodel)

    def ShowSettingsDialog(self):
        """
        Open user settings dialog and update options
        """
        options = self.options
        settings = options.GetSettings()
        result = SettingsDialog(settings, self).exec()

        if result == QDialog.Accepted:
            # Update and save global settings
            options.update(settings)
            options.Save()

            LoadStylesheet(options.get('theme'))
            logging.info("Settings updated")

    def ShowAboutDialog(self):
        result = AboutDialog(self).exec()

    def PrepareForSave(self):
        self.model_viewer.CloseProjectOptions()

    def closeEvent(self, e):
        if self.command_queue:
            self.command_queue.Stop()

        project = self.datamodel.project
        if project and project.subtitles:
            project.UpdateProjectFile()

        super().closeEvent(e)

    def _load_icon(self, name):
        if not name or name == "default":
            name = "subtrans64"
        filepath = GetResourcePath(f"{name}.ico")
        self.setWindowIcon(QIcon(filepath))

    def _on_action_requested(self, action_name, params):
        if not self.datamodel:
            raise Exception(f"Cannot perform {action_name} without a data model")

        self.statusBar().showMessage(f"Executing {action_name}")

        try:
            self.datamodel.PerformModelAction(action_name, params)

        except Exception as e:
            logging.error(f"Error in {action_name}: {str(e)}")

    def _on_command_added(self, command : Command):
        logging.debug(f"Added a {type(command).__name__} command to the queue")
        self._update_main_toolbar()
        self._update_status_bar(command)

    def _on_command_complete(self, command : Command, success):
        logging.debug(f"A {type(command).__name__} command completed (success={str(success)})")

        if success:
            if isinstance(command, LoadSubtitleFile):
                self.datamodel = command.datamodel
                self.model_viewer.SetDataModel(command.datamodel)
                if not self.datamodel.IsProjectInitialised():
                    self._show_new_project_Settings(self.datamodel.project)

            if command.model_update.HasUpdate():
                self.datamodel.UpdateViewModel(command.model_update)

            elif command.datamodel:
                # Shouldn't need to do a full model rebuild often? 
                self.datamodel = command.datamodel
                self.action_handler.SetDataModel(self.datamodel)
                self.model_viewer.SetDataModel(self.datamodel)
                self.model_viewer.show()

            else:
                self.model_viewer.hide()

        # Auto-save if the commmand queue is empty and the project has changed
        if self.datamodel and self.datamodel.NeedsAutosave():
            if not self.command_queue.AnyCommands():
                self.datamodel.SaveProject()

        self._update_status_bar(command, success)
        self._update_main_toolbar()

    def _update_status_bar(self, command : Command, succeeded : bool = None):
        if not command:
            self.statusBar().showMessage("")
        elif succeeded is None:
            self.statusBar().showMessage(f"{type(command).__name__} executed. {self.command_queue.queue_size} commands in queue.")
        elif command.aborted:
            self.statusBar().showMessage(f"{type(command).__name__} aborted.")

        else:
            if succeeded:
                if self.command_queue.queue_size > 1:
                    self.statusBar().showMessage(f"{type(command).__name__} was successful. {self.command_queue.queue_size} commands in queue.")
                elif self.command_queue.queue_size == 1:
                    self.statusBar().showMessage(f"{type(command).__name__} was successful. One command left in queue.")
                else:
                    self.statusBar().showMessage(f"{type(command).__name__} was successful.")

            else:
                self.statusBar().showMessage(f"{type(command).__name__} failed.")

    def _update_main_toolbar(self):
        self.toolbar.SetBusyStatus(self.datamodel, self.command_queue)

    def _on_project_options_changed(self, options: dict):
        if options and self.datamodel:
            self.datamodel.UpdateOptions(options)

    def _first_run(self, options: Options):
        settings = options.GetSettings()
        result = FirstRunOptions(settings, self).exec()

        if result == QDialog.Accepted:
            logging.info("First run options set")
            options.update(settings)
            options.add('firstrun', False)
            options.Save()
            self.options = options
            LoadStylesheet(options.get('theme'))

    def _show_new_project_Settings(self, project : SubtitleProject):
        result = NewProjectSettings(project, self).exec()

        if result == QDialog.Accepted:
            logging.info("Project settings set")
            self.QueueCommand(BatchSubtitlesCommand(project))

    def _on_error(self, error : object):
        logging.error(str(error))

        if isinstance(error, NoApiKeyError):
            if self.datamodel and self.datamodel.options:
                self._first_run(self.datamodel.options)