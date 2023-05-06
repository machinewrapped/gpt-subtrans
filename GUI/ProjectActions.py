from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QFileDialog, QApplication, QMainWindow, QStyle
from GUI.CommandQueue import ClearCommandQueue

from GUI.FileCommands import *
from GUI.ProjectCommands import (
    MergeBatchesCommand, 
    MergeLinesCommand, 
    MergeScenesCommand, 
    ResumeTranslationCommand, 
    SwapTextAndTranslations, 
    TranslateSceneCommand, 
    TranslateSceneMultithreadedCommand
)
from GUI.ProjectSelection import ProjectSelection
from GUI.Widgets.ModelView import ModelView

class ActionError(Exception):
    def __init__(self, message, error = None):
        super().__init__(message)
        self.error = error

    def __str__(self) -> str:
        if self.error:
            return str(self.error)
        return super().__str__()

class NoApiKeyError(ActionError):
    def __init__(self):
        super().__init__("Cannot translate without a valid OpenAI API Key")

class ProjectActions(QObject):
    issueCommand = Signal(object)
    actionError = Signal(object)

    _actions = {}

    def __init__(self, mainwindow : QMainWindow = None):
        super().__init__()
        self._mainwindow = mainwindow
        self.AddAction('Quit', self._quit, QStyle.StandardPixmap.SP_DialogCloseButton, 'Ctrl+W', 'Exit Program')
        self.AddAction('Load Subtitles', self._load_subtitle_file, QStyle.StandardPixmap.SP_DialogOpenButton)
        self.AddAction('Save Project', self._save_project_file, QStyle.StandardPixmap.SP_DialogSaveButton, 'Ctrl+S', 'Save project')
        self.AddAction('Project Options', self._toggle_project_options, QStyle.StandardPixmap.SP_FileDialogDetailedView, 'Ctrl+/', 'Project Options')
        self.AddAction('Start Translating', self._start_translating, QStyle.StandardPixmap.SP_MediaPlay, 'Ctrl+T', 'Start/Resume Translating')
        self.AddAction('Start Translating Fast', self._start_translating_fast, QStyle.StandardPixmap.SP_MediaSeekForward, 'Ctrl+Shift+T', 'Start translating on multiple threads (fast but unsafe)')
        self.AddAction('Stop Translating', self._stop_translating, QStyle.StandardPixmap.SP_MediaStop, 'Esc', 'Stop translation')

        #TODO: Mixing different concepts of "action" here, is there a better separation?
        # self.AddAction('Translate Selection', self._translate_selection, shortcut='Ctrl+T')
        # self.AddAction('Merge Selection', self._merge_selection, shortcut='Ctrl+Shift+M')
        ProjectDataModel.RegisterActionHandler('Translate Selection', self._translate_selection)
        ProjectDataModel.RegisterActionHandler('Merge Selection', self._merge_selection)
        ProjectDataModel.RegisterActionHandler('Split Batch', self._split_batch)
        ProjectDataModel.RegisterActionHandler('Swap Text', self._swap_text_and_translation)

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

    def _check_api_key(self):
        if self._mainwindow and self._mainwindow.datamodel and self._mainwindow.datamodel.options:
            options: Options = self._mainwindow.datamodel.options
            if options.api_key():
                return True
        
        self.actionError.emit(NoApiKeyError())
        return False

    def _quit(self):
        QApplication.instance().quit()

    def _load_subtitle_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self._mainwindow, "Open File", "", "Subtitle files (*.srt *.subtrans);;All Files (*)")

        if filepath:
            command = LoadSubtitleFile(filepath)
            self._issue_command(command)

    def _save_project_file(self):
        # TODO: Shouldn't have to ask the main window for the project
        project : SubtitleProject = self._mainwindow.project
        if not project:
            raise ActionError("Nothing to save!")

        filepath = project.projectfile
        if not filepath or self._is_shift_pressed():
            filepath, _ = QFileDialog.getSaveFileName(self._mainwindow, "Save Project File", filepath, "Subtrans projects (*.subtrans);;All Files (*)")

        if filepath:
            command = SaveProjectFile(project, filepath)
            self._issue_command(command)

    def _is_shift_pressed(self):
        return QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier

    def _toggle_project_options(self):
        """
        Hide or show the project options panel
        """
        # TODO: Route GUI actions with signals and events or something
        model_viewer: ModelView = self._mainwindow.model_viewer
        model_viewer.ToggleProjectOptions()

    def _start_translating(self):
        if self._check_api_key():
            self._issue_command(ResumeTranslationCommand(multithreaded=False))

    def _start_translating_fast(self):
        if self._check_api_key():
            self._issue_command(ResumeTranslationCommand(multithreaded=True))

    def _stop_translating(self):
        if self._check_api_key():
            self._issue_command(ClearCommandQueue())

    def _translate_selection(self, datamodel, selection : ProjectSelection):
        """
        Request translation of selected scenes and batches
        """
        if not selection.Any():
            raise ActionError("Nothing selected to translate")

        if not self._check_api_key():
            return
            
        logging.debug(f"Translate selection of {str(selection)}")

        for scene in selection.scenes.values():
            batch_numbers = [ batch.number for batch in selection.batches.values() if batch.selected and batch.scene == scene.number ]
            command = TranslateSceneMultithreadedCommand(scene.number, batch_numbers, datamodel)
            self._issue_command(command)

    def _merge_selection(self, datamodel, selection : ProjectSelection):
        """
        Merge selected scenes or batches (TODO: lines)
        """
        if not selection.Any():
            raise ActionError("Nothing selected to merge")
        
        if not selection.IsSequential():
            raise ActionError("Cannot merge non-sequential elements")
        
        if selection.OnlyScenes():
            self._issue_command(MergeScenesCommand(selection.scene_numbers, datamodel))

        elif selection.OnlyBatches():
            scene_number = selection.selected_batches[0].scene
            batch_numbers = [ batch.number for batch in selection.selected_batches ]
            self._issue_command(MergeBatchesCommand(scene_number, batch_numbers, datamodel))

        elif selection.AnyLines():
            self._issue_command(MergeLinesCommand(selection))

        else:
            raise ActionError(f"Unable to merge selection ({str(selection)})")
        
    def _split_batch(self, datamodel, selection : ProjectSelection):
        """
        Split a batch in two at the specified index (optionally, using a different index for translated lines)
        """
        if not selection.Any():
            raise ActionError("Please select a line to split the batch at")
        
        if selection.MultipleSelected():
            raise ActionError("Please select a single split point")
        
        scene_number, batch_number = selection.selected_batches[0]
        line_number = selection.selected_lines[0]

    def _swap_text_and_translation(self, datamodel, selection : ProjectSelection):
        """
        This is a simple action to test the GUI
        """
        if not selection.AnyBatches() or selection.MultipleSelected():
            raise ActionError("Can only swap text of a single batch")
        
        scene_number, batch_number = selection.batch_numbers[0]
    
        self._issue_command(SwapTextAndTranslations(scene_number, batch_number, datamodel))