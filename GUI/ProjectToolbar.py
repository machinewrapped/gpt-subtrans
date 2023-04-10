from PySide6.QtCore import Qt
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QToolBar, QStyle, QApplication

class ProjectToolbar(QToolBar):
    toggleOptions = Signal(bool)

    _show_options = True

    def __init__(self, parent=None):
        super().__init__("Project Toolbar", parent)

        self.setOrientation(Qt.Orientation.Vertical)
        self.setMovable(False)

        self._toggle_options_btn = QAction(self.show_options_icon, "Hide/Show Project Options", self)
        self._toggle_options_btn.triggered.connect(self._toggle_options)
        self.addAction(self._toggle_options_btn)

    def _toggle_options(self):
        self.show_options = not self.show_options
        self.toggleOptions.emit(self.show_options)

    @property
    def show_options(self):
        return self._show_options
    
    @show_options.setter
    def show_options(self, value):
        self._show_options = value
        self._toggle_options_btn.setIcon(self.show_options_icon)

    @property
    def show_options_icon(self):
        icon = QStyle.StandardPixmap.SP_ArrowLeft if self.show_options else QStyle.StandardPixmap.SP_FileDialogDetailedView
        return QApplication.style().standardIcon(icon)