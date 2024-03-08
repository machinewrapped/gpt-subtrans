import os
from PySide6.QtWidgets import (QDialog, QFormLayout, QVBoxLayout, QLabel, QDialogButtonBox, QTabWidget, QWidget, )

from GUI.ProjectViewModel import BatchItem, LineItem, SceneItem

from GUI.Widgets.OptionsWidgets import MULTILINE_OPTION, CreateOptionWidget

class EditDialog(QDialog):
    def __init__(self, model, parent=None, title=None) -> None:
        super().__init__(parent)
        self.model = model
        self.editors = {}
        self.setMinimumWidth(800)

        self.layout = QVBoxLayout(self)

        if title:
            self.setWindowTitle(title)
            self.layout.addWidget(QLabel(title))

        # Subclass populates the editor widget
        editor_widget = self.CreateEditor()

        self.layout.addWidget(editor_widget)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.buttonBox)

    def GetFormLayout(self):
        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        return layout

    def SetTabLayout(self, tab_widget : QTabWidget, layout, title : str):
        widget = QWidget()
        widget.setLayout(layout)
        tab_widget.addTab(widget, title)

    def AddDescription(self, form_layout : QFormLayout, description: str):
        """
        Add a description to the form layout
        """
        form_layout.addRow(QLabel(description))

    def AddMultilineEdit(self, form_layout : QFormLayout, key : str, read_only=False):
        """
        Add an editable field supporting multiline plaintext, optionally making it read-only
        """
        editor = CreateOptionWidget(key, self.model.get(key), MULTILINE_OPTION)
        if read_only:
            editor.SetReadOnly(True)

        form_layout.addRow(editor.key, editor)
        self.editors[key] = editor

    def UpdateModelFromEditor(self, key):
        """
        Update a field in the model with the value of the matching editor
        """
        self.model[key] = self.editors[key].GetValue()

    def CreateEditor(self):
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

    def CreateEditor(self) -> QWidget:
        form_layout = self.GetFormLayout()
        self.AddMultilineEdit(form_layout, 'summary')

        # Create widget, set layout, and return
        editor_widget = QWidget()
        editor_widget.setLayout(form_layout)
        return editor_widget

    def UpdateModel(self):
        self.UpdateModelFromEditor('summary')

class EditBatchDialog(EditDialog):
    def __init__(self, item : BatchItem, parent=None) -> None:
        self.item = item
        super().__init__(item.batch_model, parent, title=f"Scene {item.scene} Batch {item.number}")

    def CreateEditor(self):
        # Create tab widget
        tab_widget = QTabWidget()

        # Create "Summary" tab
        summary_layout = self.GetFormLayout()
        self.AddMultilineEdit(summary_layout, 'summary')
        self.SetTabLayout(tab_widget, summary_layout, "Summary")

        # Create "Response" tab if item has a response
        if self.item.response:
            response_layout = self.GetFormLayout()
            self.AddMultilineEdit(response_layout, 'response', read_only=True)
            if self.item.has_errors:
                self.AddMultilineEdit(response_layout, 'errors', read_only=True)

            self.SetTabLayout(tab_widget, response_layout, "Response")

        # Create debug tabs if DEBUG_MODE environment var is set
        if os.environ.get("DEBUG_MODE") == "1":
            prompt_layout = self.GetFormLayout()
            self.AddMultilineEdit(prompt_layout, 'prompt', read_only=True)
            self.SetTabLayout(tab_widget, prompt_layout, "Prompt")

            context_layout = self.GetFormLayout()
            self.AddMultilineEdit(context_layout, 'context', read_only=True)
            self.SetTabLayout(tab_widget, context_layout, "Context")

            messages_layout = self.GetFormLayout()
            self.AddMultilineEdit(messages_layout, 'messages', read_only=True)
            self.SetTabLayout(tab_widget, messages_layout, "Messages")

        return tab_widget

    def UpdateModel(self):
        self.UpdateModelFromEditor('summary')


class EditSubtitleDialog(EditDialog):
    def __init__(self, line : LineItem, parent=None) -> None:
        self.line = line
        self.model = {
            'original' : self.line.text if line else "",
            'translated'  : self.line.translation if line else ""
        }
        super().__init__(self.model, parent, title=f"Line {self.line.number}: {self.line.start} --> {self.line.end}")

    def CreateEditor(self) -> QWidget:
        form_layout = self.GetFormLayout()
        self.AddMultilineEdit(form_layout, 'original')
        self.AddMultilineEdit(form_layout, 'translated')

        editor_widget = QWidget()
        editor_widget.setLayout(form_layout)
        return editor_widget

    def UpdateModel(self):
        self.UpdateModelFromEditor('original')
        self.UpdateModelFromEditor('translated')
        