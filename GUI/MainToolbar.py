from PySide6.QtWidgets import QToolBar, QStyle, QApplication
from PySide6.QtGui import QAction, QIcon

from GUI.CommandQueue import CommandQueue
from GUI.GuiInterface import GuiInterface
from GUI.ProjectActions import ProjectActions
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Commands.StartTranslationCommand import StartTranslationCommand
from GUI.Commands.TranslateSceneCommand import TranslateSceneCommand

class MainToolbar(QToolBar):
    """
    Main toolbar for the application
    """
    _action_groups = [
        ["Load Subtitles", "Save Project"],
        ["Start Translating", "Start Translating Fast", "Stop Translating"],
        ["Undo", "Redo"],
        ["Settings"],
        ["About", "Quit"]
        ]

    def __init__(self,  gui_interface : GuiInterface):
        super().__init__("Main Toolbar")

        self.gui = gui_interface

        self.DefineActions()
        self.AddActionGroups()

        self.setMovable(False)

    def UpdateToolbar(self):
        """
        Update the toolbar
        """
        self.UpdateBusyStatus()
        self.UpdateTooltips()

    def DefineActions(self, action_handler : ProjectActions = None):
        """
        Define the supported actions
        """
        self._actions = {}
        action_handler : ProjectActions = self.gui.GetActionHandler()

        self.DefineAction('Quit', action_handler.exitProgram, QStyle.StandardPixmap.SP_DialogCloseButton, 'Ctrl+W', 'Exit Program')
        self.DefineAction('Load Subtitles', action_handler.LoadProject, QStyle.StandardPixmap.SP_DialogOpenButton, 'Ctrl+O', 'Load Subtitles')
        self.DefineAction('Save Project', action_handler.SaveProject, QStyle.StandardPixmap.SP_DialogSaveButton, 'Ctrl+S', 'Save project (Hold Shift to save as...)')
        self.DefineAction('Project Settings', action_handler.toggleProjectSettings, QStyle.StandardPixmap.SP_FileDialogDetailedView, 'Ctrl+/', 'Project Settings')
        self.DefineAction('Settings', action_handler.showSettings, QStyle.StandardPixmap.SP_FileDialogListView, 'Ctrl+?', 'Settings')
        self.DefineAction('Start Translating', action_handler.StartTranslating, QStyle.StandardPixmap.SP_MediaPlay, 'Ctrl+T', 'Start/Resume Translating')
        self.DefineAction('Start Translating Fast', action_handler.StartTranslatingFast, QStyle.StandardPixmap.SP_MediaSeekForward, 'Ctrl+Shift+T', 'Start translating on multiple threads (fast but unsafe)')
        self.DefineAction('Stop Translating', action_handler.StopTranslating, QStyle.StandardPixmap.SP_MediaStop, 'Esc', 'Stop translation')
        self.DefineAction("Undo", action_handler.undoLastCommand, QStyle.StandardPixmap.SP_ArrowBack, 'Ctrl+Z', 'Undo last action')
        self.DefineAction("Redo", action_handler.redoLastCommand, QStyle.StandardPixmap.SP_ArrowForward, 'Ctrl+Shift+Z', 'Redo last undone action')
        self.DefineAction('About', action_handler.showAboutDialog, QStyle.StandardPixmap.SP_MessageBoxInformation, tooltip='About this program')

    def DefineAction(self, name, function : callable, icon=None, shortcut=None, tooltip=None):
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

    def AddActionGroups(self):
        for group in self._action_groups:
            if group != self._action_groups[0]:
                self.addSeparator()

            actions = self.GetActionList(group)
            for action in actions:
                self.addAction(action)

    def EnableActions(self, action_list : list[str]):
        """
        Enable a list of commands
        """
        for action in self.actions():
            if action.text() in action_list:
                action.setEnabled(True)

    def DisableActions(self, action_list : list[str]):
        """
        Disable a list of commands
        """
        for action in self.actions():
            if action.text() in action_list:
                action.setEnabled(False)

    def SetActionsEnabled(self, action_list : list[str], enabled : bool):
        """
        Enable or disable a list of commands
        """
        for action in self.actions():
            if action.text() in action_list:
                action.setEnabled(enabled)

    def UpdateTooltip(self, action_name : str, label : str):
        """
        Update the label of a command
        """
        for action in self.actions():
            if action.text() == action_name:
                action.setToolTip(label)

    def UpdateBusyStatus(self):
        """
        Update the toolbar status based on the current state of the project
        """
        datamodel : ProjectDataModel = self.gui.GetDataModel()

        if not datamodel or not datamodel.IsProjectInitialised():
            self.DisableActions([ "Save Project", "Start Translating", "Start Translating Fast", "Stop Translating", "Undo", "Redo" ])
            self.EnableActions([ "Load Subtitles" ])
            return

        # Enable or disable toolbar commands  depending on whether any translations are ongoing
        command_queue : CommandQueue = self.gui.GetCommandQueue()
        if command_queue.Contains(type_list = [TranslateSceneCommand, StartTranslationCommand]):
            self.DisableActions([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast", "Undo", "Redo"])
            self.EnableActions([ "Stop Translating" ])
            return

        self.DisableActions("Stop Translating")

        no_blocking_commands = not command_queue.has_blocking_commands
        self.SetActionsEnabled([ "Load Subtitles", "Save Project", "Start Translating" ], no_blocking_commands)
        self.SetActionsEnabled([ "Start Translating Fast" ], no_blocking_commands and datamodel.allow_multithreaded_translation)
        self.SetActionsEnabled([ "Undo" ], no_blocking_commands and command_queue.can_undo)
        self.SetActionsEnabled([ "Redo" ], no_blocking_commands and command_queue.can_redo)

    def UpdateTooltips(self):
        """
        Update the labels on the toolbar
        """
        command_queue : CommandQueue = self.gui.GetCommandQueue()
        if command_queue.can_undo:
            last_command = command_queue.undo_stack[-1]
            self.UpdateTooltip("Undo", f"Undo {type(last_command).__name__}")
        else:
            self.UpdateTooltip("Undo", "Nothing to undo")

        if command_queue.can_redo:
            next_command = command_queue.redo_stack[-1]
            self.UpdateTooltip("Redo", f"Redo {type(next_command).__name__}")
        else:
            self.UpdateTooltip("Redo", "Nothing to redo")