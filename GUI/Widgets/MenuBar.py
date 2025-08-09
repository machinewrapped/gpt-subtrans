from PySide6.QtWidgets import QMenuBar, QMenu
from PySubtitle.Helpers.Localization import _

class ProjectMenuBar(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        file_menu = QMenu(_("File"), self)
        self.addMenu(file_menu)

        edit_menu = QMenu(_("Edit"), self)
        self.addMenu(edit_menu)

        tools_menu = QMenu(_("Tools"), self)
        self.addMenu(tools_menu)

