from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QTextEdit

import logging

class LogWindow(QTextEdit):
    level_colors = {
        "DEBUG": QColor(135, 206, 250),  # Light blue
        "INFO": QColor(255, 255, 255),   # White
        "WARNING": QColor(255, 255, 0),  # Yellow
        "ERROR": QColor(255, 0, 0)       # Red
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

        self.qt_log_handler = QtLogHandler(self)
        self.qt_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt=r"%A, %H:%M:%S"))

        root_logger = logging.getLogger()
        root_logger.addHandler(self.qt_log_handler)

    def SetLoggingLevel(self, level):
        self.qt_log_handler.setLevel(level)

    def AppendLogMessage(self, message, level):
        text_cursor = self.textCursor()
        text_cursor.movePosition(QTextCursor.End)

        text_format = QTextCharFormat()
        text_format.setForeground(self.level_colors.get(level, QColor(0, 0, 0)))

        text_cursor.insertText(f"{message}\n", text_format)

class QtLogHandler(logging.Handler):
    log_window: LogWindow

    def __init__(self, log_window):
        super().__init__()
        self.setLevel(logging.INFO)
        self.log_window = log_window

    def emit(self, record):
        msg = self.format(record)
        level = record.levelname
        self.log_window.AppendLogMessage(msg, level)

