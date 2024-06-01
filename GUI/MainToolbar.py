from PySide6.QtWidgets import QToolBar
from GUI.CommandQueue import CommandQueue

from GUI.GuiInterface import GuiInterface
from GUI.ProjectActions import ProjectActions
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Commands.ResumeTranslationCommand import ResumeTranslationCommand
from GUI.Commands.TranslateSceneCommand import TranslateSceneCommand, TranslateSceneMultithreadedCommand

class MainToolbar(QToolBar):
    """
    Main toolbar for the application
    """
    _action_groups = [ ["Load Subtitles", "Save Project"], ["Start Translating", "Start Translating Fast", "Stop Translating"], ["Undo", "Redo"], ["Settings"], ["About", "Quit"] ]

    def __init__(self,  gui_interface : GuiInterface):
        super().__init__("Main Toolbar")

        self.gui = gui_interface

        action_handler : ProjectActions = gui_interface.GetActionHandler()

        self.setMovable(False)

        for group in self._action_groups:
            if group != self._action_groups[0]:
                self.addSeparator()

            actions = action_handler.GetActionList(group)
            for action in actions:
                self.addAction(action)

    def UpdateToolbar(self):
        """
        Update the toolbar
        """
        self.UpdateBusyStatus()
        self.UpdateTooltips()

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

    def SetCommandsEnabled(self, action_list : list[str], enabled : bool):
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
        if command_queue.Contains(type_list = [TranslateSceneCommand, TranslateSceneMultithreadedCommand, ResumeTranslationCommand]):
            self.DisableActions([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast", "Undo", "Redo"])
            self.EnableActions([ "Stop Translating" ])
            return

        self.DisableActions("Stop Translating")

        no_blocking_commands = not command_queue.has_blocking_commands
        self.SetCommandsEnabled([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast" ], no_blocking_commands)
        self.SetCommandsEnabled([ "Undo" ], no_blocking_commands and command_queue.can_undo)
        self.SetCommandsEnabled([ "Redo" ], no_blocking_commands and command_queue.can_redo)

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