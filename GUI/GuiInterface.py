import logging
import os

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QDialog,
    QMessageBox
)

from GUI.AboutDialog import AboutDialog
from GUI.Command import Command
from GUI.CommandQueue import ClearCommandQueue, CommandQueue
from GUI.Commands.BatchSubtitlesCommand import BatchSubtitlesCommand
from GUI.Commands.LoadSubtitleFile import LoadSubtitleFile
from GUI.Commands.SaveProjectFile import SaveProjectFile
from GUI.FirstRunOptions import FirstRunOptions
from GUI.GUICommands import CheckProviderSettings, ExitProgramCommand
from GUI.GuiHelpers import LoadStylesheet
from GUI.NewProjectSettings import NewProjectSettings
from GUI.ProjectActions import ProjectActions
from GUI.ProjectDataModel import ProjectDataModel
from GUI.SettingsDialog import SettingsDialog
from PySubtitle.Options import Options
from PySubtitle.SubtitleError import ProviderConfigurationError
from PySubtitle.TranslationProvider import TranslationProvider
from PySubtitle.VersionCheck import CheckIfUpdateAvailable, CheckIfUpdateCheckIsRequired
from PySubtitle.version import __version__

class GuiInterface(QObject):
    """
    Interface to interact with the GUI
    """
    dataModelChanged = Signal(object)
    commandAdded = Signal(object)
    commandComplete = Signal(object, bool)
    commandUndone = Signal(object)
    actionRequested = Signal(str)
    prepareForSave = Signal()
    toggleProjectSettings = Signal()

    def __init__(self, mainwindow : QMainWindow, options : Options):
        super().__init__()

        self.mainwindow = mainwindow

        if not options:
            options = Options()
            options.InitialiseInstructions()
            options.LoadSettings()

        options.add('available_providers', sorted(TranslationProvider.get_providers()))

        self.global_options = options

        # Create the project data model
        self.datamodel = ProjectDataModel(options=options)

        # Create the command queue
        self.command_queue = CommandQueue(mainwindow)
        self.command_queue.SetMaxThreadCount(options.get('max_threads', 1))
        self.command_queue.commandExecuted.connect(self._on_command_complete, Qt.ConnectionType.QueuedConnection)
        self.command_queue.commandAdded.connect(self._on_command_added, Qt.ConnectionType.QueuedConnection)
        self.command_queue.commandUndone.connect(self._on_command_undone, Qt.ConnectionType.QueuedConnection)

        # Create centralised action handler
        self.action_handler = ProjectActions()
        self.action_handler.issueCommand.connect(self.QueueCommand)
        self.action_handler.actionError.connect(self._on_error)
        self.action_handler.undoLastCommand.connect(self.UndoLastCommand)
        self.action_handler.redoLastCommand.connect(self.RedoLastCommand)
        self.action_handler.showSettings.connect(self.ShowSettingsDialog)
        self.action_handler.showProviderSettings.connect(self.ShowProviderSettingsDialog)
        self.action_handler.toggleProjectSettings.connect(self.toggleProjectSettings)
        self.action_handler.saveSettings.connect(self.SaveSettings)
        self.action_handler.loadProject.connect(self.LoadProject)
        self.action_handler.saveProject.connect(self.SaveProject)
        self.action_handler.showAboutDialog.connect(self.ShowAboutDialog)
        self.action_handler.exitProgram.connect(self._exit_program)

        if self.global_options.get('last_used_path'):
            self.action_handler.last_used_path = self.global_options.get('last_used_path')

    def GetMainWindow(self) -> QMainWindow:
        """
        Get a reference to the application main window
        """
        return self.mainwindow

    def QueueCommand(self, command : Command, callback = None, undo_callback = None):
        """
        Add a command to the command queue and set the datamodel
        """
        self.command_queue.AddCommand(command, self.datamodel, callback=callback, undo_callback=undo_callback)

    def UndoLastCommand(self):
        """
        Undo the last command
        """
        if not self.command_queue.can_undo:
            logging.error("Cannot undo the last command")
            return

        try:
            self.command_queue.UndoLastCommand()

        except Exception as e:
            logging.error(f"Error undoing the last command: {str(e)}")
            self.command_queue.ClearUndoStack()

    def RedoLastCommand(self):
        """
        Redo the last command
        """
        if not self.command_queue.can_redo:
            logging.error("Cannot redo the last command")
            return

        try:
            self.command_queue.RedoLastCommand()

        except Exception as e:
            logging.error(f"Error redoing the last command: {str(e)}")

    def GetCommandQueue(self):
        """
        Get the command queue
        """
        return self.command_queue

    def GetDataModel(self):
        """
        Get the data model
        """
        return self.datamodel

    def SetDataModel(self, datamodel : ProjectDataModel):
        """
        Set the data model
        """
        self.datamodel = datamodel
        self.action_handler.SetDataModel(datamodel)
        self.dataModelChanged.emit(datamodel)

    def PerformModelAction(self, action_name : str, params : dict):
        """
        Perform an action on the data model
        """
        if not self.datamodel:
            raise Exception(f"Cannot perform {action_name} without a data model")

        try:
            self.actionRequested.emit(action_name)
            self.datamodel.PerformModelAction(action_name, params)

        except Exception as e:
            logging.error(f"Error in {action_name}: {str(e)}")

    def GetActionHandler(self):
        """
        Get the action handler
        """
        return self.action_handler

    def ShowSettingsDialog(self):
        """
        Open user settings dialog and update options
        """
        provider_cache = self.datamodel.provider_cache if self.datamodel else None
        dialog = SettingsDialog(self.global_options, provider_cache=provider_cache, parent=self.GetMainWindow())
        result = dialog.exec()

        if result == QDialog.Accepted:
            self.UpdateSettings(dialog.settings)

            logging.info("Settings updated")

    def ShowProviderSettingsDialog(self):
        """
        Open the settings dialog with the provider settings focused
        """
        provider_cache = self.datamodel.provider_cache if self.datamodel else None
        dialog = SettingsDialog(self.global_options, provider_cache=provider_cache, parent=self.GetMainWindow(), focus_provider_settings=True)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.UpdateSettings(dialog.settings)

    def SaveSettings(self):
        """
        Save the global settings
        """
        self.prepareForSave.emit()
        self.global_options.SaveSettings()

    def UpdateSettings(self, settings : dict):
        """
        Update the global settings and project settings, and save if required
        """
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

    def UpdateProjectSettings(self, settings : dict):
        """
        Update the project settings
        """
        if settings:
            self.datamodel.UpdateProjectSettings(settings)

    def Startup(self, filepath : str = None):
        """
        Perform startup tasks
        """
        options = self.global_options

        LoadStylesheet(options.theme)

        if options.provider is None or options.get('firstrun'):
            # Configure critical settings
            self._first_run(options)
        elif filepath:
            # Load file if we were opened with one
            filepath = os.path.abspath(filepath)
            self.LoadProject(filepath)
        else:
            # Check if the translation provider is configured correctly
            self.QueueCommand(CheckProviderSettings(options))

        logging.info(f"GUI-Subtrans {__version__}")

        # Check if there is a more recent version on Github (TODO: make this optional)
        if CheckIfUpdateCheckIsRequired():
            CheckIfUpdateAvailable()

    def PrepareToExit(self):
        """
        Clear the command queue and exit the program
        """
        if self.command_queue and self.command_queue.has_commands:
            self.QueueCommand(ClearCommandQueue())
            self.command_queue.Stop()

        project = self.datamodel.project
        if project and project.subtitles:
            project.UpdateProjectFile()

    def LoadProject(self, filepath : str):
        """
        Load a project file
        """
        self.QueueCommand(LoadSubtitleFile(filepath, self.global_options), callback=self._on_project_loaded)

    def SaveProject(self, filepath : str = None):
        """
        Save the project file
        """
        self.QueueCommand(SaveProjectFile(self.datamodel.project, filepath), callback=self._on_project_saved)

    def ShowNewProjectSettings(self, datamodel : ProjectDataModel):
        """
        Show the new project settings dialog
        """
        try:
            dialog = NewProjectSettings(datamodel, parent=self.GetMainWindow())

            if dialog.exec() == QDialog.Accepted:
                datamodel.UpdateProjectSettings(dialog.settings)
                self.QueueCommand(CheckProviderSettings(datamodel.project_options))
                self.QueueCommand(BatchSubtitlesCommand(datamodel.project, datamodel.project_options))
                logging.info("Project settings set")

        except Exception as e:
            logging.error(f"Error initialising project settings: {str(e)}")

    def ShowAboutDialog(self):
        """
        Show the about dialog
        """
        _ = AboutDialog(parent=self.GetMainWindow()).exec()

    def _on_command_added(self, command : Command):
        """
        Handle the addition of a command to the queue
        """
        logging.debug(f"Added a {type(command).__name__} command to the queue")
        self.commandAdded.emit(command)

    def _on_command_undone(self, command : Command):
        """
        Handle the undoing of a command
        """
        logging.debug(f"{type(command).__name__} command undone")
        for model_update in command.model_updates:
            self.datamodel.UpdateViewModel(model_update)

        command.ClearModelUpdates()

        self.commandUndone.emit(command)

    def _on_command_complete(self, command : Command, success):
        """
        Handle the completion of a command
        """
        if isinstance(command, ExitProgramCommand):
            QApplication.instance().quit()
            return

        logging.debug(f"A {type(command).__name__} command {'succeeded' if success else 'failed'}")

        if success:
            if command.model_updates:
                for model_update in command.model_updates:
                    self.datamodel.UpdateViewModel(model_update)

                command.ClearModelUpdates()

            elif command.datamodel != self.datamodel:
                # Shouldn't need to do a full model rebuild often?
                self.SetDataModel(command.datamodel)

            elif command.datamodel is None:
                self.dataModelChanged.emit(None)

        # Auto-save if the commmand queue is empty and the project has changed
        if self.datamodel and self.datamodel.NeedsAutosave():
            if not self.command_queue.has_commands:
                self.datamodel.SaveProject()

        self.commandComplete.emit(command, success)

    def _on_project_loaded(self, command : LoadSubtitleFile):
        """
        Update the data model and last used path after loading a project
        """
        self.SetDataModel(command.datamodel)
        self._update_last_used_path(command.filepath)
        if not self.datamodel.IsProjectInitialised():
            self.ShowNewProjectSettings(self.datamodel)

    def _on_project_saved(self, command : SaveProjectFile):
        """
        Update the data model and last used path after saving a project
        """
        self._update_last_used_path(command.filepath)
        self.SetDataModel(command.datamodel)

    def _update_last_used_path(self, filepath : str):
        """
        Update the last used path in the global options
        """
        self.action_handler.last_used_path = self.global_options.get('last_used_path')
        self.global_options.add('last_used_path', os.path.dirname(filepath))
        self.global_options.SaveSettings()

    def _first_run(self, options: Options):
        """
        First run initialisation
        """
        if not options.available_providers:
            logging.error("No translation providers available. Please install one or more providers.")
            QMessageBox.critical(self, "Error", "No translation providers available. Please install one or more providers.")
            self.QueueCommand(ExitProgramCommand())
            return

        first_run_options = FirstRunOptions(options, parent = self.GetMainWindow())
        result = first_run_options.exec()

        if result == QDialog.Accepted:
            logging.info("First run options set")
            initial_settings = first_run_options.GetSettings()
            self.UpdateSettings(initial_settings)

            self.QueueCommand(CheckProviderSettings(options))

    def _on_error(self, error : object):
        """
        Handle an error from the action handler
        """
        logging.error(str(error))

        if isinstance(error, ProviderConfigurationError):
            if self.datamodel and self.datamodel.project_options:
                logging.warning("Please configure the translation provider settings")
                self.ShowProviderSettingsDialog()

    def _exit_program(self):
        self.PrepareToExit()
        self.QueueCommand(ExitProgramCommand())
