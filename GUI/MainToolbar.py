from PySide6.QtWidgets import QToolBar

from GUI.ProjectActions import ProjectActions

class MainToolbar(QToolBar):
    _action_groups = [ ["Load Subtitles", "Save Project"], ["Quit"] ]

    def __init__(self,  handler : ProjectActions):
        super().__init__("Main Toolbar")

        self.setMovable(False)

        for group in self._action_groups:
            if group != self._action_groups[0]:
                self.addSeparator()

            handlers = handler.GetActionList(group)
            for action in handlers:
                self.addAction(action)

