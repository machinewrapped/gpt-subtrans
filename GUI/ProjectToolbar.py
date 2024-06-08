from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QToolBar, QStyle, QApplication

from GUI.ProjectActions import ProjectActions

class ProjectToolbar(QToolBar):
    _show_options = True

    def __init__(self, action_handler : ProjectActions, parent=None):
        super().__init__("Project Toolbar", parent)

        self.setOrientation(Qt.Orientation.Vertical)
        self.setMovable(False)

        self.action_handler = action_handler

        self._toggle_options_btn = QAction(self.show_setting_icon, "Hide/Show Project Options", self)
        self._toggle_options_btn.triggered.connect(self._toggle_settings)
        self.addAction(self._toggle_options_btn)

    def _toggle_settings(self):
        self.show_settings = not self.show_settings
        self.action_handler.ShowProjectSettings(self.show_settings)

    @property
    def show_settings(self):
        return self._show_options

    @show_settings.setter
    def show_settings(self, value):
        self._show_options = value
        self._toggle_options_btn.setIcon(self.show_setting_icon)

    @property
    def show_setting_icon(self):
        icon : QIcon = QStyle.StandardPixmap.SP_ArrowLeft if self.show_settings else QStyle.StandardPixmap.SP_FileDialogDetailedView
        return QApplication.style().standardIcon(icon)