import logging
import os

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QFileDialog, QApplication, QMainWindow, QStyle

from GUI.Command import Command
from GUI.CommandQueue import ClearCommandQueue

from GUI.GUICommands import CheckProviderSettings
from GUI.Commands.AutoSplitBatchCommand import AutoSplitBatchCommand
from GUI.Commands.DeleteLinesCommand import DeleteLinesCommand
from GUI.Commands.MergeBatchesCommand import MergeBatchesCommand
from GUI.Commands.MergeLinesCommand import MergeLinesCommand
from GUI.Commands.MergeScenesCommand import MergeScenesCommand
from GUI.Commands.ReparseTranslationsCommand import ReparseTranslationsCommand
from GUI.Commands.ResumeTranslationCommand import ResumeTranslationCommand
from GUI.Commands.SaveProjectFile import SaveProjectFile
from GUI.Commands.SplitBatchCommand import SplitBatchCommand
from GUI.Commands.SplitSceneCommand import SplitSceneCommand
from GUI.Commands.SwapTextAndTranslations import SwapTextAndTranslations
from GUI.Commands.TranslateSceneCommand import TranslateSceneCommand, TranslateSceneMultithreadedCommand

from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectSelection import ProjectSelection

from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleValidator import SubtitleValidator

class ActionError(Exception):
    def __init__(self, message, error = None):
        super().__init__(message)
        self.error = error

    def __str__(self) -> str:
        if self.error:
            return str(self.error)
        return super().__str__()

class ProjectActions(QObject):
    issueCommand = Signal(object)
    actionError = Signal(object)
    undoLastCommand = Signal()
    redoLastCommand = Signal()
    saveSettings = Signal()
    showSettings = Signal()
    showProviderSettings = Signal()
    toggleProjectSettings = Signal()
    showAboutDialog = Signal()
    loadProject = Signal(str)
    saveProject = Signal(str)
    exitProgram = Signal()

    _actions = {}

    def __init__(self, mainwindow : QMainWindow = None, datamodel : ProjectDataModel = None):
        super().__init__()

        self._mainwindow = mainwindow
        self.datamodel = datamodel
        self.last_used_path = os.path.dirname(datamodel.project.projectfile) if datamodel and datamodel.project else None

        self.AddAction('Quit', self.exitProgram, QStyle.StandardPixmap.SP_DialogCloseButton, 'Ctrl+W', 'Exit Program')
        self.AddAction('Load Subtitles', self._load_project, QStyle.StandardPixmap.SP_DialogOpenButton, 'Ctrl+O', 'Load Subtitles')
        self.AddAction('Save Project', self._save_project, QStyle.StandardPixmap.SP_DialogSaveButton, 'Ctrl+S', 'Save project (Hold Shift to save as...)')
        self.AddAction('Project Settings', self.toggleProjectSettings, QStyle.StandardPixmap.SP_FileDialogDetailedView, 'Ctrl+/', 'Project Settings')
        self.AddAction('Settings', self.showSettings, QStyle.StandardPixmap.SP_FileDialogListView, 'Ctrl+?', 'Settings')
        self.AddAction('Start Translating', self._start_translating, QStyle.StandardPixmap.SP_MediaPlay, 'Ctrl+T', 'Start/Resume Translating')
        self.AddAction('Start Translating Fast', self._start_translating_fast, QStyle.StandardPixmap.SP_MediaSeekForward, 'Ctrl+Shift+T', 'Start translating on multiple threads (fast but unsafe)')
        self.AddAction('Stop Translating', self._stop_translating, QStyle.StandardPixmap.SP_MediaStop, 'Esc', 'Stop translation')
        self.AddAction("Undo", self.undoLastCommand, QStyle.StandardPixmap.SP_ArrowBack, 'Ctrl+Z', 'Undo last action')
        self.AddAction("Redo", self.redoLastCommand, QStyle.StandardPixmap.SP_ArrowForward, 'Ctrl+Sift+Z', 'Redo last undone action')
        self.AddAction('About', self.showAboutDialog, QStyle.StandardPixmap.SP_MessageBoxInformation, tooltip='About this program')

        #TODO: Mixing different concepts of "action" here - should just be able to pass a ProjectActions instance around

        # self.AddAction('Translate Selection', self._translate_selection, shortcut='Ctrl+T')
        # self.AddAction('Merge Selection', self._merge_selection, shortcut='Ctrl+Shift+M')
        ProjectDataModel.RegisterActionHandler('Validate Provider Settings', self._check_provider_settings)
        ProjectDataModel.RegisterActionHandler('Show Provider Settings', self._show_provider_settings)
        ProjectDataModel.RegisterActionHandler('Translate Selection', self._translate_selection)
        ProjectDataModel.RegisterActionHandler('Reparse Translation', self._reparse_selection)
        ProjectDataModel.RegisterActionHandler('Update Scene', self._update_scene)
        ProjectDataModel.RegisterActionHandler('Update Batch', self._update_batch)
        ProjectDataModel.RegisterActionHandler('Update Line', self._update_line)
        ProjectDataModel.RegisterActionHandler('Merge Selection', self._merge_selection)
        ProjectDataModel.RegisterActionHandler('Delete Selection', self._delete_selection)
        ProjectDataModel.RegisterActionHandler('Split Batch', self._split_batch)
        ProjectDataModel.RegisterActionHandler('Split Scene', self._split_scene)
        ProjectDataModel.RegisterActionHandler('Auto-Split Batch', self._autosplit_batch)
        ProjectDataModel.RegisterActionHandler('Swap Text', self._swap_text_and_translation)

        #TODO: ProjectDataModel.RegisterActionHandler('Auto-split line', self._autosplit_line)      - this would not be safe if the line/batch is translated
        #TODO: ProjectDataModel.RegisterActionHandler('Auto-break line', self._autobreak_line)

    def SetDataModel(self, datamodel : ProjectDataModel):
        self.datamodel = datamodel

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

    def _load_project(self):
        """
        Load a subtitle file
        """
        initial_path = self.last_used_path
        filters = "Subtitle files (*.srt *.subtrans);;All Files (*)"
        filepath, _ = QFileDialog.getOpenFileName(parent=self._mainwindow, caption="Open File", dir=initial_path, filter=filters)

        if filepath:
            self.loadProject.emit(filepath)

    def _save_project(self):
        """
        Save the current project
        """
        project : SubtitleProject = self.datamodel.project
        if not project:
            raise ActionError("Nothing to save!")

        self.saveSettings.emit()

        filepath = project.projectfile
        show_dialog = self._is_shift_pressed()

        if show_dialog or not filepath or not os.path.exists(filepath):
            filepath = os.path.join(self.last_used_path, os.path.basename(project.projectfile))
            filepath, _ = QFileDialog.getSaveFileName(self._mainwindow, "Save Project File", filepath, "Subtrans projects (*.subtrans);;All Files (*)")

        if filepath:
            self.saveProject.emit(filepath)

    def _is_shift_pressed(self):
        return QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier

    def _check_provider_settings(self, datamodel : ProjectDataModel):
        """
        Check if the translation provider is configured correctly.
        """
        self._issue_command(CheckProviderSettings(datamodel.project_options))

    def _show_provider_settings(self, datamodel : ProjectDataModel):
        """
        Show the settings dialog for the translation provider
        """
        self.showProviderSettings.emit()

    def _validate_datamodel(self, datamodel : ProjectDataModel):
        """
        Validate that there is a datamodel with subtitles that have been batched
        """
        if not datamodel or not datamodel.project:
            raise ActionError("Project is not valid")

        if not datamodel.project.subtitles:
            raise ActionError("No subtitles")

        if not datamodel.project.subtitles.scenes:
            raise ActionError("Subtitles have not been batched")

    def _start_translating(self):
        """
        Start or resume translation of the project
        """
        datamodel : ProjectDataModel = self.datamodel
        self._validate_datamodel(datamodel)

        self.saveSettings.emit()

        if datamodel.project.needsupdate:
            datamodel.project.WriteProjectFile()

        self._issue_command(ResumeTranslationCommand(multithreaded=False))

    def _start_translating_fast(self):
        """
        Start or resume translation of the project using multiple threads
        """
        datamodel : ProjectDataModel = self.datamodel
        self._validate_datamodel(datamodel)

        self.saveSettings.emit()

        if datamodel.project.needsupdate:
            datamodel.project.WriteProjectFile()

        self._issue_command(ResumeTranslationCommand(multithreaded=True))

    def _stop_translating(self):
        """
        Stop the translation process
        """
        self._issue_command(ClearCommandQueue())

    def _translate_selection(self, datamodel : ProjectDataModel, selection : ProjectSelection):
        """
        Request translation of selected scenes and batches
        """
        if not selection.Any():
            raise ActionError("Nothing selected to translate")

        self._validate_datamodel(datamodel)

        if datamodel.project.needsupdate:
            datamodel.project.WriteProjectFile()

        logging.debug(f"Translate selection of {str(selection)}")

        multithreaded = len(selection.scenes) > 1 and datamodel.project_options.allow_multithreaded_translation

        for scene in selection.scenes.values():
            line_numbers = [ line.number for line in selection.selected_lines if line.scene == scene.number ]

            if line_numbers:
                # Extract unique batch numbers from the selected lines
                batch_numbers = list(set([ line.batch for line in selection.selected_lines if line.scene == scene.number ]))
            else:
                batch_numbers = [ batch.number for batch in selection.batches.values() if batch.selected and batch.scene == scene.number ]

            if multithreaded:
                command = TranslateSceneMultithreadedCommand(scene.number, batch_numbers, line_numbers, datamodel)
            else:
                command = TranslateSceneCommand(scene.number, batch_numbers, line_numbers, datamodel)

            self._issue_command(command)

    def _reparse_selection(self, datamodel : ProjectDataModel, selection : ProjectSelection):
        """
        Reparse selected batches
        """
        if not selection.AnyBatches():
            raise ActionError("Nothing selected to reparse")

        self._validate_datamodel(datamodel)

        batch_numbers = [ (batch.scene, batch.number) for batch in selection.selected_batches ]
        line_numbers = [ line.number for line in selection.selected_lines ]
        command = ReparseTranslationsCommand(batch_numbers, line_numbers, datamodel)
        self._issue_command(command)

    def _update_scene(self, datamodel : ProjectDataModel, scene_number : int, update : dict):
        """
        Update the user-updatable properties of a subtitle scene
        """
        logging.debug(f"Updating scene {scene_number} with {str(update)}")

        self._validate_datamodel(datamodel)

        subtitles : SubtitleFile = datamodel.project.subtitles
        if subtitles.UpdateScene(scene_number, update):
            datamodel.project.needsupdate = True

    def _update_batch(self, datamodel : ProjectDataModel, scene_number : int, batch_number : int, update : dict):
        """
        Update the user-updatable properties of a subtitle batch
        """
        logging.debug(f"Updating scene {scene_number} batch {batch_number} with {str(update)}")

        self._validate_datamodel(datamodel)

        subtitles : SubtitleFile = datamodel.project.subtitles
        if subtitles.UpdateBatch(scene_number, batch_number, update):
            datamodel.project.needsupdate = True

    def _update_line(self, datamodel : ProjectDataModel, line_number : int, original_text : str, translated_text : str):
        """
        Update the user-updatable properties of a subtitle batch
        """
        logging.debug(f"Updating line {line_number} with {str(original_text)} > {str(translated_text)}")

        self._validate_datamodel(datamodel)

        subtitles : SubtitleFile = datamodel.project.subtitles

        subtitles.UpdateLineText(line_number, original_text, translated_text)
        datamodel.project.needsupdate = True

        batch = subtitles.GetBatchContainingLine(line_number)
        if batch:
            if batch.errors:
                validator = SubtitleValidator(datamodel.project_options)
                self.errors = validator.ValidateBatch(batch)

            update = {
                'lines' : { line_number : { 'text' : original_text, 'translation' : translated_text}},
                'errors' : batch.errors,
            }

            datamodel.viewmodel.UpdateBatch(batch.scene, batch.number, update)

    def _merge_selection(self, datamodel, selection : ProjectSelection):
        """
        Merge selected scenes, batches or lines
        """
        if not selection.Any():
            raise ActionError("Nothing selected to merge")

        if not selection.IsContiguous():
            raise ActionError("Cannot merge non-sequential elements")

        if selection.OnlyScenes():
            self._issue_command(MergeScenesCommand(selection.scene_numbers, datamodel))

        elif selection.OnlyBatches():
            scene_number = selection.selected_batches[0].scene
            batch_numbers = [ batch.number for batch in selection.selected_batches ]
            self._issue_command(MergeBatchesCommand(scene_number, batch_numbers, datamodel))

        elif selection.AnyLines():
            self._issue_command(MergeLinesCommand(selection.selected_lines))

        else:
            raise ActionError(f"Unable to merge selection ({str(selection)})")

    def _delete_selection(self, datamodel : ProjectDataModel, selection : ProjectSelection):
        """
        Delete scenes, batches or lines from the project
        """
        self._validate_datamodel(datamodel)

        if not selection.Any():
            raise ActionError("Nothing selected to delete")

        if not selection.AnyLines():
            raise ActionError("Cannot delete scenes or batches yet")

        line_numbers = [ line.number for line in selection.selected_lines ]
        self._issue_command(DeleteLinesCommand(line_numbers, datamodel))

    def _split_batch(self, datamodel, selection : ProjectSelection):
        """
        Split a batch in two at the specified index (optionally, using a different index for translated lines)
        """
        if not selection.Any():
            raise ActionError("Please select a line to split the batch at")

        if selection.MultipleSelected():
            raise ActionError("Please select a single split point")

        selected_line = selection.selected_lines[0]

        self._issue_command(SplitBatchCommand(selected_line.scene, selected_line.batch, selected_line.number))

    def _split_scene(self, datamodel, selection : ProjectSelection):
        """
        Split a batch in two at the specified index (optionally, using a different index for translated lines)
        """
        if not selection.AnyBatches():
            raise ActionError("Please select a batch to split the scene at")

        if selection.MultipleSelected():
            raise ActionError("Please select a single split point")

        selected_batch = selection.selected_batches[0]

        self._issue_command(SplitSceneCommand(selected_batch.scene, selected_batch.number))

    def _autosplit_batch(self, datamodel, selection : ProjectSelection):
        """
        Split a batch in two automatically (using heuristics to find the best split point)
        """
        if not selection.AnyBatches() or selection.MultipleSelected():
            raise ActionError("Can only autosplit a single batch")

        scene_number, batch_number = selection.selected_batches[0].key

        self._issue_command(AutoSplitBatchCommand(scene_number, batch_number))

    def _swap_text_and_translation(self, datamodel, selection : ProjectSelection):
        """
        This is a simple action to test the GUI
        """
        if not selection.AnyBatches() or selection.MultipleSelected():
            raise ActionError("Can only swap text of a single batch")

        scene_number, batch_number = selection.batch_numbers[0]

        self._issue_command(SwapTextAndTranslations(scene_number, batch_number, datamodel))