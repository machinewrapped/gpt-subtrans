from PySide6.QtCore import Signal
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QGridLayout
)

from GUI.ProjectViewModel import LineItem

class TreeViewItemWidget(QFrame):
    def __init__(self, content, parent=None):
        super(TreeViewItemWidget, self).__init__(parent)

        layout = QVBoxLayout()
        if content.get('heading'):
            layout.addWidget(WidgetHeader(content['heading'], parent=self))

        if content.get('subheading'):
            layout.addWidget(WidgetSubheading(content['subheading'], parent=self))

        if content.get('body'):
            layout.addWidget(WidgetBody(content['body'], parent=self))

        self.setLayout(layout)

class WidgetHeader(QLabel):
    def __init__(self, text, parent=None):
        super(WidgetHeader, self).__init__(parent)
        self.setText(text)

class WidgetSubheading(QLabel):
    def __init__(self, text, parent=None):
        super(WidgetSubheading, self).__init__(parent)
        self.setText(text)

class WidgetBody(QLabel):
    def __init__(self, text, parent=None):
        super(WidgetBody, self).__init__(parent)
        # self.setReadOnly(True)
        # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setText(text)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWordWrap(True)

class LineItemView(QWidget):
    def __init__(self, line, parent=None):
        super(LineItemView, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(LineItemHeader(line, parent=self))
        layout.addWidget(LineItemBody(line, parent=self))

        self.setLayout(layout)

class LineItemHeader(QLabel):
    def __init__(self, line: LineItem, parent=None):
        super(LineItemHeader, self).__init__(parent)
        self.setText(f"{str(line.number)}, {str(line.start)} --> {str(line.end)}")

class LineItemBody(QLabel):
    def __init__(self, line: LineItem, parent=None):
        super(LineItemBody, self).__init__(parent)
        self.setText(line.text)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWordWrap(True)

class OptionsGrid(QGridLayout):
    """
    Grid layout for options (styling class)
    """
    def __init__(self, parent = None) -> None:
        super().__init__(parent)

class TextBoxEditor(QTextEdit):
    """
    Multi-line editor that provides a signal when text contents change
    """
    editingFinished = Signal(str)

    _original = None

    def focusInEvent(self, e) -> None:
        self._original = self.toPlainText()
        return super().focusInEvent(e)

    def focusOutEvent(self, e) -> None:
        text = self.toPlainText()
        if text != self._original:
            self.editingFinished.emit(text)
        return super().focusOutEvent(e)

