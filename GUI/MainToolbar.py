from PySide6.QtWidgets import QToolBar
from GUI.CommandQueue import CommandQueue

from GUI.GuiInterface import GuiInterface
from GUI.ProjectActions import ProjectActions
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Commands.ResumeTranslationCommand import ResumeTranslationCommand
from GUI.Commands.TranslateSceneCommand import TranslateSceneCommand, TranslateSceneMultithreadedCommand

class MainToolbar(QToolBar):
    # _action_groups = [ ["Load Subtitles", "Save Project"], ["Start Translating", "Stop Translating"], ["Quit"] ]
    _action_groups = [ ["Load Subtitles", "Save Project"], ["Start Translating", "Start Translating Fast", "Stop Translating"], ["Settings"], ["About", "Quit"] ]

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

    def EnableActions(self, action_list):
        for action in self.actions():
            if action.text() in action_list:
                action.setEnabled(True)

    def DisableActions(self, action_list):
        for action in self.actions():
            if action.text() in action_list:
                action.setEnabled(False)

    def UpdateBusyStatus(self):
        datamodel : ProjectDataModel = self.gui.GetDataModel()

        if not datamodel or not datamodel.IsProjectInitialised():
            self.DisableActions([ "Save Project", "Start Translating", "Start Translating Fast", "Stop Translating" ])
            self.EnableActions([ "Load Subtitles" ])
            return

        # Enable or disable toolbar commands  depending on whether any translations are ongoing
        command_queue : CommandQueue = self.gui.GetCommandQueue()
        if command_queue.Contains(type_list = [TranslateSceneCommand, TranslateSceneMultithreadedCommand, ResumeTranslationCommand]):
            self.DisableActions([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast"])
            self.EnableActions([ "Stop Translating" ])
            return

        self.DisableActions("Stop Translating")

        if command_queue.AnyBlocking():
            self.DisableActions([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast" ])
            return

        self.EnableActions([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast" ])
