import dotenv

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
)
from GUI.Command import Command
from GUI.GuiInterface import GuiInterface
from GUI.MainToolbar import MainToolbar
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Widgets.LogWindow import LogWindow
from GUI.Widgets.ModelView import ModelView
from PySubtitle.Helpers.Resources import GetResourcePath
from PySubtitle.Options import Options
from PySubtitle.version import __version__

# Load environment variables from .env file
dotenv.load_dotenv()

class MainWindow(QMainWindow):
    def __init__(self, parent=None, options : Options = None, filepath : str = None):
        super().__init__(parent)

        self.setWindowTitle("GUI-Subtrans")
        self.setGeometry(100, 100, 1600, 900)
        self._load_icon("gui-subtrans")

        self.gui_interface = GuiInterface(self, options)
        self.gui_interface.actionRequested.connect(self._on_action_requested, Qt.ConnectionType.QueuedConnection)
        self.gui_interface.commandAdded.connect(self._on_command_added, Qt.ConnectionType.QueuedConnection)
        self.gui_interface.commandComplete.connect(self._on_command_complete, Qt.ConnectionType.QueuedConnection)
        self.gui_interface.commandUndone.connect(self._on_command_undone, Qt.ConnectionType.QueuedConnection)
        self.gui_interface.dataModelChanged.connect(self._on_data_model_changed, Qt.ConnectionType.QueuedConnection)
        self.gui_interface.prepareForSave.connect(self._prepare_for_save, Qt.ConnectionType.QueuedConnection)
        self.gui_interface.toggleProjectSettings.connect(self._toggle_project_settings, Qt.ConnectionType.QueuedConnection)

        # Create the main widget
        main_widget = QWidget(self)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # Create the toolbar
        self.toolbar = MainToolbar(self.gui_interface)
        self.toolbar.UpdateBusyStatus()
        main_layout.addWidget(self.toolbar)

        # Create a splitter widget to divide the remaining vertical space between the project viewer and log window
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)

        self.model_viewer = ModelView(self.gui_interface, parent=splitter)
        self.model_viewer.settingsChanged.connect(self.gui_interface.UpdateProjectSettings)
        splitter.addWidget(self.model_viewer)

        # Create the log window widget and add it to the splitter
        log_window_widget = LogWindow(splitter)
        splitter.addWidget(log_window_widget)
        splitter.setSizes([int(self.height() * 0.8), int(self.height() * 0.2)])

        # Run startup tasks
        self.gui_interface.Startup(filepath)

        self.statusBar().showMessage("Ready.")

    def closeEvent(self, e):
        self._prepare_for_save()
        self.gui_interface.PrepareToExit()

        super().closeEvent(e)

    def _prepare_for_save(self):
        """
        Update project settings and close the panel
        """
        if self.model_viewer:
            self.model_viewer.ShowProjectSettings(False)

    def _on_data_model_changed(self, datamodel : ProjectDataModel):
        """
        Update the model viewer with the new data model or hide it if there is no data model
        """
        if datamodel:
            self.model_viewer.SetDataModel(datamodel)
            self.model_viewer.show()
        else:
            self.model_viewer.hide()

    def _load_icon(self, name):
        if not name or name == "default":
            name = "subtrans64"
        filepath = GetResourcePath("assets", f"{name}.ico")
        self.setWindowIcon(QIcon(filepath))

    def _on_action_requested(self, action_name : str):
        self.statusBar().showMessage(f"Performing {action_name}")

    def _on_command_added(self, command : Command):
        self.toolbar.UpdateBusyStatus()
        self._update_status_bar(command)

    def _on_command_complete(self, command : Command, success):
        self.toolbar.UpdateBusyStatus()
        self._update_status_bar(command, succeeded=success)

    def _on_command_undone(self, command : Command):
        self.toolbar.UpdateBusyStatus()
        self._update_status_bar(command, undone=True)

    def _update_status_bar(self, command : Command, succeeded : bool = None, undone : bool = False):
        command_queue = self.gui_interface.GetCommandQueue()

        if not command:
            self.statusBar().showMessage("")
        elif undone:
            self.statusBar().showMessage(f"{type(command).__name__} undone.")
        elif succeeded is None:
            self.statusBar().showMessage(f"{type(command).__name__} executed. {command_queue.queue_size} commands in queue.")
        elif command.aborted:
            self.statusBar().showMessage(f"{type(command).__name__} aborted.")
        elif not succeeded:
            self.statusBar().showMessage(f"{type(command).__name__} failed.")
        else:
            if command_queue.queue_size > 1:
                self.statusBar().showMessage(f"{type(command).__name__} was successful. {command_queue.queue_size} commands in queue.")
            elif command_queue.queue_size == 1:
                self.statusBar().showMessage(f"{type(command).__name__} was successful. One command left in queue.")
            else:
                self.statusBar().showMessage(f"{type(command).__name__} was successful.")

    def _toggle_project_settings(self, show = None):
        self.model_viewer.ShowProjectSettings(show)

