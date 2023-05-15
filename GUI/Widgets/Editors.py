import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QFormLayout)
from GUI.ProjectViewModel import BatchItem, SceneItem

from GUI.Widgets.OptionsWidgets import MULTILINE_OPTION, CreateOptionWidget

class EditDialog(QDialog):
    def __init__(self, model, parent=None, title=None) -> None:
        super().__init__(parent)
        self.model = model
        self.editors = {}
        self.setMinimumWidth(512)

        self.layout = QVBoxLayout(self)

        if title:
            self.setWindowTitle(title)
            self.layout.addWidget(QLabel(title))

        self.form_layout = QFormLayout()
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Subclass populates the form
        self.CreateForm()

        self.layout.addLayout(self.form_layout)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.buttonBox)

    def AddMultilineEdit(self, key : str, read_only=False):
        """
        Add an editable field supporting multiline plaintext, optionally making it read-only
        """
        editor = CreateOptionWidget(key, self.model.get(key), MULTILINE_OPTION)
        if read_only:
            editor.SetReadOnly(True)

        self.editors[key] = editor
        self.form_layout.addRow(editor.key, editor)

    def UpdateModelFromEditor(self, key):
        """
        Update a field in the model with the value of the matching editor
        """
        self.model[key] = self.editors[key].GetValue()

    def CreateForm(self):
        """
        Subclasses should override this method to add editable fields to the form layout
        """
        raise Exception("Not implemented in this class")
    
    def UpdateModel(self):
        """
        Subclasses should override this method to update the model from the form
        """
        raise Exception("Not implemented in this class")

    def accept(self):
        self.UpdateModel()
        return super().accept()

class EditSceneDialog(EditDialog):
    def __init__(self, item : SceneItem, parent=None) -> None:
        self.item = item
        super().__init__(item.scene_model, parent, title=f"Scene {item.number}")

    def CreateForm(self):
        self.AddMultilineEdit('summary')

    def UpdateModel(self):
        self.UpdateModelFromEditor('summary')

class EditBatchDialog(EditDialog):
    def __init__(self, item : BatchItem, parent=None) -> None:
        self.item = item
        super().__init__(item.batch_model, parent, title=f"Scene {item.scene} Batch {item.number}")

    def CreateForm(self):
        self.AddMultilineEdit('summary')

        if os.environ.get("DEBUG_MODE") == "1":
            self.AddMultilineEdit('context', read_only=True)
            self.AddMultilineEdit('errors', read_only=True)

    def UpdateModel(self):
        self.UpdateModelFromEditor('summary')
