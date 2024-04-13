import os
import logging
import dotenv

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QDialog,
    QMessageBox
)
from GUI.AboutDialog import AboutDialog
from GUI.Command import Command
from GUI.CommandQueue import ClearCommandQueue, CommandQueue
from GUI.Commands.LoadSubtitleFile import LoadSubtitleFile
from GUI.FirstRunOptions import FirstRunOptions
from GUI.GUICommands import CheckProviderSettings, ExitProgramCommand
from GUI.GuiHelpers import LoadStylesheet
from GUI.MainToolbar import MainToolbar
from GUI.SettingsDialog import SettingsDialog
from GUI.ProjectActions import ProjectActions
from GUI.Commands.BatchSubtitlesCommand import BatchSubtitlesCommand
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Widgets.LogWindow import LogWindow
from GUI.Widgets.ModelView import ModelView
from GUI.NewProjectSettings import NewProjectSettings
from PySubtitle.Helpers.resources import GetResourcePath
from PySubtitle.Options import Options
from PySubtitle.SubtitleError import ProviderConfigurationError
from PySubtitle.TranslationProvider import TranslationProvider
from PySubtitle.VersionCheck import CheckIfUpdateAvailable, CheckIfUpdateCheckIsRequired
from PySubtitle.version import __version__

# Load environment variables from .env file
dotenv.load_dotenv()

class MainWindow(QMainWindow):
    def __init__(self, parent=None, options : Options = None, filepath : str = None):
        super().__init__(parent)

        self.setWindowTitle("GUI-Subtrans")
        self.setGeometry(100, 100, 1600, 900)
        self._load_icon("gui-subtrans")

        if not options:
            options = Options()
            options.InitialiseInstructions()
            options.LoadSettings()

        options.add('available_providers', sorted(TranslationProvider.get_providers()))

        # TODO: move global_options to the datamodel?
        self.global_options = options

        LoadStylesheet(options.theme)

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
        self.action_handler.saveSettings.connect(self._prepare_for_save)
        self.action_handler.showSettings.connect(self._show_settings_dialog)
        self.action_handler.showProviderSettings.connect(self._show_provider_settings_dialog)
        self.action_handler.toggleProjectSettings.connect(self._toggle_project_settings)
        self.action_handler.showAboutDialog.connect(self._show_about_dialog)
        self.action_handler.loadSubtitleFile.connect(self._load_subtitle_file)

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
        self.model_viewer.settingsChanged.connect(self._on_project_settings_changed)
        self.model_viewer.actionRequested.connect(self._on_action_requested)
        splitter.addWidget(self.model_viewer)

        # Create the log window widget and add it to the splitter
        log_window_widget = LogWindow(splitter)
        splitter.addWidget(log_window_widget)
        splitter.setSizes([int(self.height() * 0.8), int(self.height() * 0.2)])

        if options.provider is None or options.get('firstrun'):
            # Configure critical settings
            self._first_run(options)
        elif filepath:
            # Load file if we were opened with one
            filepath = os.path.abspath(filepath)
            self.QueueCommand(LoadSubtitleFile(filepath, options))
        else:
            # Check if the translation provider is configured correctly
            self.QueueCommand(CheckProviderSettings(options))

        logging.info(f"GUI-Subtrans {__version__}")

        # Check if there is a more recent version on Github (TODO: make this optional)
        if CheckIfUpdateCheckIsRequired():
            CheckIfUpdateAvailable()

        self.statusBar().showMessage("Ready.")

    def QueueCommand(self, command : Command):
        """
        Add a command to the command queue and set the datamodel
        """
        self.command_queue.AddCommand(command, self.datamodel)

    def _show_settings_dialog(self):
        """
        Open user settings dialog and update options
        """
        provider_cache = self.datamodel.provider_cache if self.datamodel else None
        dialog = SettingsDialog(self.global_options, provider_cache=provider_cache, parent=self)
        result = dialog.exec()

        if result == QDialog.Accepted:
            self._update_settings(dialog.settings)

            logging.info("Settings updated")

    def _show_provider_settings_dialog(self):
        """
        Open the settings dialog with the provider settings focused
        """
        provider_cache = self.datamodel.provider_cache if self.datamodel else None
        dialog = SettingsDialog(self.global_options, provider_cache=provider_cache, parent=self, focus_provider_settings=True)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self._update_settings(dialog.settings)

    def _first_run(self, options: Options):
        if not options.available_providers:
            logging.error("No translation providers available. Please install one or more providers.")
            QMessageBox.critical(self, "Error", "No translation providers available. Please install one or more providers.")
            self.QueueCommand(ExitProgramCommand())
            return

        first_run_options = FirstRunOptions(options, self)
        result = first_run_options.exec()

        if result == QDialog.Accepted:
            logging.info("First run options set")
            initial_settings = first_run_options.GetSettings()
            self._update_settings(initial_settings)

            self.QueueCommand(CheckProviderSettings(options))

    def _show_new_project_Settings(self, datamodel : ProjectDataModel):
        try:
            dialog = NewProjectSettings(datamodel, self)

            if dialog.exec() == QDialog.Accepted:
                datamodel.UpdateProjectSettings(dialog.settings)
                self.QueueCommand(CheckProviderSettings(datamodel.project_options))
                self.QueueCommand(BatchSubtitlesCommand(datamodel.project, datamodel.project_options))
                logging.info("Project settings set")

        except Exception as e:
            logging.error(f"Error initialising project settings: {str(e)}")

    def _show_about_dialog(self):
        _ = AboutDialog(self).exec()

    def _update_settings(self, settings):
        updated_settings = {k: v for k, v in settings.items() if v != self.global_options.get(k)}

        if not updated_settings:
            return

        # Update and save global settings
        self.global_options.update(updated_settings)
        self.global_options.SaveSettings()

        # Update the project and provider settings
        self.datamodel.UpdateSettings(updated_settings)

        if not self.datamodel.ValidateProviderSettings():
            logging.warning("Translation provider settings are not valid. Please check the settings.")

        if 'theme' in updated_settings:
            LoadStylesheet(self.global_options.theme)
    
    def _load_subtitle_file(self, filepath):
        self.QueueCommand(LoadSubtitleFile(filepath, self.global_options))

    def _prepare_for_save(self):
        if self.model_viewer and self.datamodel:
            self.model_viewer.CloseSettings()

    def closeEvent(self, e):
        if self.command_queue and self.command_queue.AnyCommands():
            self.QueueCommand(ClearCommandQueue())
            self.QueueCommand(ExitProgramCommand())
            self.command_queue.Stop()

        self._prepare_for_save()

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
        if isinstance(command, ExitProgramCommand):
            QApplication.instance().quit()
            return

        logging.debug(f"A {type(command).__name__} command {'succeeded' if success else 'failed'}")

        if success:
            if isinstance(command, LoadSubtitleFile):
                self.datamodel = command.datamodel
                self.model_viewer.SetDataModel(command.datamodel)
                if not self.datamodel.IsProjectInitialised():
                    self._show_new_project_Settings(self.datamodel)

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

    def _toggle_project_settings(self, show = None):
        self.model_viewer.ToggleProjectSettings(show)

    def _on_project_settings_changed(self, settings: dict):
        if settings and self.datamodel:
            self.datamodel.UpdateProjectSettings(settings)

    def _on_error(self, error : object):
        logging.error(str(error))

        if isinstance(error, ProviderConfigurationError):
            if self.datamodel and self.datamodel.project_options:
                logging.warning("Please configure the translation provider settings")
                self._show_provider_settings_dialog()