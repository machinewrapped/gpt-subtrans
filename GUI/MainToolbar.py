from PySide6.QtWidgets import QToolBar
from GUI.CommandQueue import CommandQueue

from GUI.ProjectActions import ProjectActions
from GUI.ProjectCommands import ResumeTranslationCommand, TranslateSceneCommand, TranslateSceneMultithreadedCommand
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleProject import SubtitleProject

class MainToolbar(QToolBar):
    # _action_groups = [ ["Load Subtitles", "Save Project"], ["Start Translating", "Stop Translating"], ["Quit"] ]
    _action_groups = [ ["Load Subtitles", "Save Project"], ["Start Translating", "Start Translating Fast", "Stop Translating"], ["Settings"], ["About", "Quit"] ]

    def __init__(self,  handler : ProjectActions):
        super().__init__("Main Toolbar")

        self.setMovable(False)

        for group in self._action_groups:
            if group != self._action_groups[0]:
                self.addSeparator()

            handlers = handler.GetActionList(group)
            for action in handlers:
                self.addAction(action)

    def EnableActions(self, action_list):
        for action in self.actions():
            if action.text() in action_list:
                action.setEnabled(True) 

    def DisableActions(self, action_list):
        for action in self.actions():
            if action.text() in action_list:
                action.setEnabled(False) 

    def SetBusyStatus(self, datamodel : ProjectDataModel, command_queue : CommandQueue):
        if not datamodel or not datamodel.IsProjectInitialised():
            self.DisableActions([ "Save Project", "Start Translating", "Start Translating Fast", "Stop Translating" ])
            self.EnableActions([ "Load Subtitles" ])
            return
        
        # Enable or disable toolbar commands  depending on whether any translations are ongoing
        if command_queue.Contains(type_list = [TranslateSceneCommand, TranslateSceneMultithreadedCommand, ResumeTranslationCommand]):
            self.DisableActions([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast"])
            self.EnableActions([ "Stop Translating" ])
            return
        
        self.DisableActions("Stop Translating")

        if command_queue.AnyBlocking():
            self.DisableActions([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast" ])
            return
        
        self.EnableActions([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast" ])
