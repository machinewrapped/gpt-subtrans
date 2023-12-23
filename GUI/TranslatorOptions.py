import logging
from PySide6.QtWidgets import (
    QStyle, 
    QApplication, 
    QFormLayout, 
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QFileDialog, 
    )
from GUI.GuiHelpers import GetResourcePath
from GUI.Widgets.OptionsWidgets import MULTILINE_OPTION, CreateOptionWidget

from PySubtitle.Options import Options
from PySubtitle.Instructions import Instructions
from PySubtitle.SubtitleTranslator import SubtitleTranslator

class TranslatorOptionsDialog(QDialog):
    def __init__(self, data : dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Translator Options")
        self.setMinimumWidth(800)

        self.model = data.get('model', '')
        self.models = SubtitleTranslator.GetAvailableModels(data.get('api_key'), data.get('api_base'))

        self.instructions : Instructions = Instructions(data)

        self.form_layout = QFormLayout()
        self.model_edit = self._add_form_option("model", self.model, self.models, tooltip="Model to use for translation")
        self.prompt_edit = self._add_form_option("prompt", self.instructions.prompt, str, "Prompt for each translation request")
        self.instructions_edit = self._add_form_option("instructions", self.instructions.instructions, MULTILINE_OPTION, "System instructions for the translator")
        self.retry_instructions_edit = self._add_form_option("retry_instructions", self.instructions.retry_instructions, MULTILINE_OPTION, "Supplementary instructions when retrying")

        self.button_layout = QHBoxLayout()

        self.load_button = self._create_button("Load Instructions", self._load_instructions)
        self.save_button = self._create_button("Save Instructions", self._save_instructions)
        self.default_button = self._create_button("Defaults", self.set_defaults)
        self.ok_button = self._create_button("OK", self.accept)
        self.cancel_button = self._create_button("Cancel", self.reject)

        layout = QVBoxLayout()
        layout.addLayout(self.form_layout)
        layout.addLayout(self.button_layout)

        self.setLayout(layout)

    def _add_form_option(self, key, initial_value, key_type, tooltip = None):
        input = CreateOptionWidget(key, initial_value, key_type, tooltip)
        self.form_layout.addRow(key, input)
        return input

    def _create_button(self, text, on_click):
        button = QPushButton(text)
        button.clicked.connect(on_click)
        self.button_layout.addWidget(button)
        return button

    def accept(self):
        self.model = self.model_edit.GetValue()

        if self._check_for_edited_instructions():
            self.instructions.prompt = self.prompt_edit.GetValue()
            self.instructions.instructions = self.instructions_edit.GetValue()
            self.instructions.retry_instructions = self.retry_instructions_edit.GetValue()
            self.instructions.instruction_file = None

        super().accept()

    def reject(self):
        super().reject()

    def _check_for_edited_instructions(self):
        '''Check if the instructions have been edited'''
        if self.prompt_edit.GetValue() != self.instructions.prompt:
            return True
        if self.instructions_edit.GetValue() != self.instructions.instructions:
            return True
        if self.retry_instructions_edit.GetValue() != self.instructions.retry_instructions:
            return True

    @property
    def load_icon(self):
        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)
    
    @property
    def save_icon(self):
        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
    
    def _load_instructions(self):
        '''Load instructions from a file'''
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Instructions", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            try:
                self.instructions.LoadInstructionsFile(file_name)

                self.prompt_edit.SetValue(self.instructions.prompt)
                self.instructions_edit.SetValue(self.instructions.instructions)
                self.retry_instructions_edit.SetValue(self.instructions.retry_instructions)

            except Exception as e:
                logging.error(f"Unable to read instruction file: {str(e)}")

    def _save_instructions(self):
        '''Save instructions to a file'''
        options = QFileDialog.Options()
        filepath = GetResourcePath(self.instructions.instruction_file)
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Instructions", filepath, "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            try:
                self.instructions.prompt = self.prompt_edit.GetValue()
                self.instructions.instructions = self.instructions_edit.GetValue()
                self.instructions.retry_instructions = self.retry_instructions_edit.GetValue()
                
                self.instructions.SaveInstructions(file_name)

            except Exception as e:
                logging.error(f"Unable to write instruction file: {str(e)}")

    def set_defaults(self):
        options = Options()
        self.model_edit.SetValue(options.get('model'))
        self.prompt_edit.SetValue(options.get('prompt'))
        self.instructions_edit.SetValue(options.get('instructions'))
        self.retry_instructions_edit.SetValue(options.get('retry_instructions'))
