from PySide6.QtCore import Slot
from PySide6.QtWidgets import QToolBar, QFileDialog, QApplication
from PySide6.QtGui import QAction

from GUI.FileCommands import *

class ProjectToolbar(QToolBar):
    def __init__(self, command_queue = None):
        super().__init__()
        self.command_queue = command_queue
        self.setMovable(False)

    def quit(self):
        QApplication.intance().quit()

