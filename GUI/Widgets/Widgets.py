from PySide6.QtCore import Signal
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QGridLayout,
    QSizePolicy
)

from GUI.ProjectViewModel import LineItem

class TreeViewItemWidget(QFrame):
    def __init__(self, content, parent=None):
        super(TreeViewItemWidget, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        properties = content.get('properties', {})

        layout = QVBoxLayout()
        if content.get('heading'):
            header_widget = WidgetHeader(content['heading'], parent=self)
            self._set_properties(header_widget, properties)
            layout.addWidget(header_widget)

        if content.get('subheading'):
            subheading_widget = WidgetSubheading(content['subheading'], parent=self)
            self._set_properties(subheading_widget, properties)
            layout.addWidget(subheading_widget)

        if content.get('body'):
            body_widget = WidgetBody(content['body'], parent=self)
            self._set_properties(body_widget, properties)
            layout.addWidget(body_widget)

        self._set_properties(self, properties)
        self.setLayout(layout)

    def _set_properties(self, widget : QWidget, properties : dict):
        for key, value in properties.items():
            widget.setProperty(key, value)


class WidgetHeader(QLabel):
    def __init__(self, text, parent=None):
        super(WidgetHeader, self).__init__(parent)
        self.setText(text)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

class WidgetSubheading(QLabel):
    def __init__(self, text, parent=None):
        super(WidgetSubheading, self).__init__(parent)
        self.setText(text)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

class WidgetBody(QLabel):
    def __init__(self, text, parent=None):
        super(WidgetBody, self).__init__(parent)
        self.setText(text)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWordWrap(True)

class LineItemView(QWidget):
    def __init__(self, line, parent=None):
        super(LineItemView, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(LineItemHeader(line, parent=self))
        h_layout = QHBoxLayout()
        h_layout.addWidget(LineItemBody(line.text, parent=self))
        h_layout.addWidget(LineItemBody(line.translation or "", parent=self))
        layout.addLayout(h_layout)

        self.setLayout(layout)

class LineItemHeader(QLabel):
    def __init__(self, line: LineItem, parent=None):
        super(LineItemHeader, self).__init__(parent)
        self.setText(f"[{str(line.number)}] {str(line.start)} --> {str(line.end)}   ({str(line.duration)})")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

class LineItemBody(QLabel):
    def __init__(self, text: str, parent=None):
        super(LineItemBody, self).__init__(parent)
        self.setText(text)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
    
    def SetText(self, text):
        self.setText(text)
        self.setPlainText(text)

