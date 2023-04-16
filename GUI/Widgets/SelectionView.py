from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout, QPushButton, QSizePolicy

from GUI.ProjectSelection import ProjectSelection

def _show(widget, condition):
    if condition:
        widget.show()
    else:
        widget.hide()

class SelectionView(QFrame):
    actionRequested = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()

        self._label = QLabel(self)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        #TODO: Translate / Retranslate
        self._translate_button = QPushButton("Translate Selection", self)
        self._translate_button.clicked.connect(self._on_translate_selection)

        self._merge_scenes_button = QPushButton("Merge Scenes", self)
        self._merge_scenes_button.clicked.connect(self._on_merge_selection)

        self._merge_batches_button = QPushButton("Merge Batches", self)
        self._merge_batches_button.clicked.connect(self._on_merge_selection)

        self._swap_text_button = QPushButton("Swap Text", self)
        self._swap_text_button.clicked.connect(self._on_swap_text)

        self.ShowSelection(ProjectSelection())

        layout = QHBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(self._swap_text_button)
        layout.addWidget(self._merge_scenes_button)
        layout.addWidget(self._merge_batches_button)
        layout.addWidget(self._translate_button)

        self.setLayout(layout)

    def ShowSelection(self, selection : ProjectSelection):
        self.selection = selection

        self._label.setText(str(selection))

        _show(self._translate_button, selection.originals)
        _show(self._merge_scenes_button, selection.OnlyScenes() and selection.MultipleSelected() and selection.SelectionIsSequential())
        _show(self._merge_batches_button, selection.OnlyBatches() and selection.MultipleSelected() and selection.SelectionIsSequential())
        # _show(self._swap_text_button, selection.AnyBatches() and not selection.MultipleSelected())
        _show(self._swap_text_button, False)

    def _on_translate_selection(self):
        if self.selection:
            self.actionRequested.emit('Translate Selection', (self.selection,))

    def _on_merge_selection(self):
        if self.selection:
            self.actionRequested.emit('Merge Selection', (self.selection,))

    def _on_swap_text(self):
        if self.selection:
            self.actionRequested.emit('Swap Text', (self.selection,))


