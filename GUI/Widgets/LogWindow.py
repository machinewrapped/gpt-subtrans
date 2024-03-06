import logging

from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Signal

class LogWindow(QTextEdit):
    level_colors = {
        "DEBUG": QColor(135, 206, 250),  # Light blue
        "INFO": QColor(255, 255, 255),   # White
        "WARNING": QColor(255, 255, 0),  # Yellow
        "ERROR": QColor(255, 0, 0)       # Red
    }

    scrollToBottom = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)

        self.qt_log_handler = QtLogHandler(self)
        self.qt_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt=r"%A, %H:%M:%S"))

        root_logger = logging.getLogger()
        root_logger.addHandler(self.qt_log_handler)

        self.scrollToBottom.connect(self._scroll_to_bottom)

    def SetLoggingLevel(self, level):
        self.qt_log_handler.setLevel(level)

    def AppendLogMessage(self, message, level):
        current_scroll = self.verticalScrollBar().value()
        maximum_scroll = self.verticalScrollBar().maximum()
        scroll_to_bottom = (current_scroll == maximum_scroll) or self.textCursor().atEnd()

        text_cursor = self.textCursor()
        text_cursor.movePosition(QTextCursor.End)

        text_format = QTextCharFormat()
        text_format.setForeground(self.level_colors.get(level, QColor(0, 0, 0)))

        text_cursor.insertText(f"{message}\n", text_format)

        # Scroll to the bottom if it was at the bottom before adding the new message
        if scroll_to_bottom:
            self.scrollToBottom.emit()

    def _scroll_to_bottom(self):
        try:
            maximum_scroll = self.verticalScrollBar().maximum()
            self.verticalScrollBar().setValue(maximum_scroll)
        except:
            pass

class QtLogHandler(logging.Handler):
    log_window: LogWindow

    def __init__(self, log_window):
        super().__init__()
        self.setLevel(logging.INFO)
        self.log_window = log_window

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname
            self.log_window.AppendLogMessage(msg, level)

        except Exception:
            self.handleError(record)

