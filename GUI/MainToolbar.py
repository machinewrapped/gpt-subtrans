from PySide6.QtWidgets import QToolBar

from GUI.ProjectActions import ProjectActions

class MainToolbar(QToolBar):
    _action_groups = [ ["Load Subtitles", "Save Project"], ["Start Translating", "Stop Translating"], ["Quit"] ]
    # _action_groups = [ ["Load Subtitles", "Save Project"], ["Start Translating", "Start Translating Fast", "Stop Translating"], ["Quit"] ]

    def __init__(self,  handler : ProjectActions):
        super().__init__("Main Toolbar")

        self.setMovable(False)

        for group in self._action_groups:
            if group != self._action_groups[0]:
                self.addSeparator()

            handlers = handler.GetActionList(group)
            for action in handlers:
                self.addAction(action)

    def EnableTranslatingCommands(self):
        for action in self.actions():
            if action.text() in [ "Start Translating", "Start Translating Fast" ]:
                action.setEnabled(True)

            if action.text() in [ "Stop Translating" ]:
                action.setEnabled(False)

    def DisableTranslatingCommands(self, enable_stop = False):
        for action in self.actions():
            if action.text() in [ "Start Translating", "Start Translating Fast" ]:
                action.setEnabled(False)
            
            if action.text() in [ "Stop Translating" ]:
                action.setEnabled(enable_stop)
    