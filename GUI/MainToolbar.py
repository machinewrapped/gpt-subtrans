from PySide6.QtWidgets import QToolBar

from GUI.ProjectActions import ProjectActions

class MainToolbar(QToolBar):
    _actions = [ "Load Subtitles", "Save Project", "Quit" ]

    def __init__(self,  handler : ProjectActions):
        super().__init__("Main Toolbar")

        self.setMovable(False)

        # TODO: add action groups
        handlers = handler.GetActionList(self._actions)
        for action in handlers:
            self.addAction(action)

