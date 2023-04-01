import logging
import dotenv

from PySide6.QtGui import QAction
from PySide6.QtUiTools import QUiLoader

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog
)

from GUI.CommandQueue import CommandQueue
from GUI.FileCommands import LoadProjectFile
from GUI.ProjectDataModel import ProjectDataModel
from GUI.SubtransGuiMain import Ui_MainWindow

dotenv.load_dotenv()

class ProjectMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the window title
        self.setWindowTitle("GUI-Subtrans")

        # Create the project data model
        self.datamodel = ProjectDataModel()

        # Create the command queue
        self.command_queue = CommandQueue(datamodel=self.datamodel)
        self.command_queue.command_executed.connect(self.on_command_complete)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.toolbar.command_queue = self.command_queue

        # Set up the status bar
        self.statusBar().showMessage("Ready.")

        # TEMP
        self.command_queue.add_command(LoadProjectFile('C:/Development/Projects/GPT/gpt-subtrans/A Hero Never Dies (1998) [FR.1080p].fr.subtrans'))

    def on_command_complete(self, command, success):
        if success:
            self.statusBar().showMessage(f"{type(command).__name__} was successful.")

            if not self.datamodel or not self.datamodel.project:
                return

            if self.ui.sceneViewer:
                viewmodel = self.datamodel.CreateViewModel()
                self.ui.sceneViewer.populate(viewmodel)

        else:
            self.statusBar().showMessage(f"{type(command).__name__} failed.")


    def openProjectFile(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Subtrans Project files (*.subtrans);;All Files (*)")

        if filepath:
            command = LoadProjectFile(filepath)
            self.command_queue.add_command(command)
