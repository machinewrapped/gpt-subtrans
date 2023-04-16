from PySide6.QtWidgets import QMenuBar, QMenu

class ProjectMenuBar(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        file_menu = QMenu("File", self)
        self.addMenu(file_menu)

        edit_menu = QMenu("Edit", self)
        self.addMenu(edit_menu)

        tools_menu = QMenu("Tools", self)
        self.addMenu(tools_menu)

