from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel
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

class SubtitleItemView(QFrame):
    def __init__(self, subtitle, parent=None):
        super(SubtitleItemView, self).__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(SubtitleHeader(subtitle, parent=self))
        layout.addWidget(SubtitleBody(subtitle, parent=self))

        self.setLayout(layout)

class SubtitleHeader(QLabel):
    def __init__(self, subtitle: SubtitleItem, parent=None):
        super(SubtitleHeader, self).__init__(parent)
        self.setText(f"{str(subtitle.index)}, {str(subtitle.start)} --> {str(subtitle.end)}")

class SubtitleBody(QLabel):
    def __init__(self, subtitle: SubtitleItem, parent=None):
        super(SubtitleBody, self).__init__(parent)
        self.setText(subtitle.text)
        self.setWordWrap(True)

