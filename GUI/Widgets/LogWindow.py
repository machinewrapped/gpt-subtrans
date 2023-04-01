from PySide6.QtWidgets import QTextEdit

class LogWindow(QTextEdit):
    def __init__(self, parent = None):
        super().__init__(parent)
