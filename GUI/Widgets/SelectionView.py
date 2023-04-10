import logging
from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout, QPushButton, QSizePolicy

from GUI.ProjectSelection import ProjectSelection

class SelectionView(QFrame):
    def __init__(self) -> None:
        super().__init__()

        self._label = QLabel(self)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        self._translate_button = QPushButton("Translate Selection", self)
        self._translate_button.clicked.connect(self._translate_selection)

        self.ShowSelection(ProjectSelection())

        layout = QHBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(self._translate_button)

        self.setLayout(layout)

    def ShowSelection(self, selection : ProjectSelection):
        self._label.setText(str(selection))
        if selection.subtitles:
            self._translate_button.show()
        else:
            self._translate_button.hide()

    def _translate_selection(self):
        logging.info("Translate selection pushed")