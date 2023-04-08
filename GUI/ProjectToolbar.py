from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar

from GUI.ProjectActions import ProjectActions

class ProjectToolbar(QToolBar):
    _actions = [ "Load Subtitles", "Save Project", "Project Options", "Quit" ]

    def __init__(self,  handler : ProjectActions):
        super().__init__("Project Toolbar")

        self.setMovable(False)

        # TODO: add action groups
        handlers = handler.GetActionList(self._actions)
        for action in handlers:
            self.addAction(action)

