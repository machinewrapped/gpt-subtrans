from GUI.GuiHelpers import GetLineHeight
from PySubtitle.Helpers import UpdateFields
from PySubtitle.Helpers.Text import Linearise

from GUI.ViewModel.ViewModelError import ViewModelError

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem

class LineItem(QStandardItem):
    def __init__(self, line_number : int, model : dict):
        super(LineItem, self).__init__(f"Line {line_number}")
        self.number = line_number
        self.line_model = model
        self.height = max(GetLineHeight(self.text), GetLineHeight(self.translation)) if self.translation else GetLineHeight(self.text)

        self.setData(self.line_model, Qt.ItemDataRole.UserRole)

    def Update(self, line_update : dict):
        if not isinstance(line_update, dict):
            raise ViewModelError(f"Expected a dictionary, got a {type(line_update).__name__}")

        UpdateFields(self.line_model, line_update, ['start', 'end', 'text', 'translation'])

        if line_update.get('number'):
            self.number = line_update['number']

        self.height = max(GetLineHeight(self.text), GetLineHeight(self.translation)) if self.translation else GetLineHeight(self.text)

        self.setData(self.line_model, Qt.ItemDataRole.UserRole)

    def __str__(self) -> str:
        return f"{self.number}: {self.start} --> {self.end} | {Linearise(self.text)}"

    def __repr__(self) -> str:
        return f"{self.number}: {self.start} --> {self.end}"

    @property
    def start(self) -> str:
        return self.line_model['start']

    @property
    def end(self) -> str:
        return self.line_model['end']

    @property
    def duration(self) -> str:
        return self.line_model['duration']

    @property
    def gap(self) -> str:
        return self.line_model['gap']

    @property
    def text(self) -> str:
        return self.line_model['text']

    @property
    def translation(self) -> str:
        return self.line_model.get('translation')

    @property
    def scene(self) -> int:
        return self.line_model.get('scene')

    @property
    def batch(self) -> int:
        return self.line_model.get('batch')