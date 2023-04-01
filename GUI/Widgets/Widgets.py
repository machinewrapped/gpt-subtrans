from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel
)

from PySide6.QtWidgets import (
    QVBoxLayout, 
    QWidget, 
    QLabel, 
    QTextEdit, 
    QSizePolicy
)

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

