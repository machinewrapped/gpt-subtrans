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

from GUI.ProjectViewModel import SubtitleItem

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

class SubtitleItemView(QWidget):
    def __init__(self, subtitle, parent=None):
        super(SubtitleItemView, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(SubtitleHeader(subtitle, parent=self))
        layout.addWidget(SubtitleBody(subtitle, parent=self))

        self.setLayout(layout)

class SubtitleHeader(QLabel):
    def __init__(self, subtitle: SubtitleItem, parent=None):
        super(SubtitleHeader, self).__init__(parent)
        self.setText(f"{str(subtitle.number)}, {str(subtitle.start)} --> {str(subtitle.end)}")

class SubtitleBody(QLabel):
    def __init__(self, subtitle: SubtitleItem, parent=None):
        super(SubtitleBody, self).__init__(parent)
        self.setText(subtitle.text)
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

