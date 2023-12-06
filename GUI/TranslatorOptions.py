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
from GUI.Widgets.OptionsWidgets import MULTILINE_OPTION, CreateOptionWidget

from PySubtitle.Options import Options
from PySubtitle.SubtitleTranslator import SubtitleTranslator

class TranslatorOptionsDialog(QDialog):
    def __init__(self, data : dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Translator Options")
        self.setMinimumWidth(800)

        self.data = data
        self.models = SubtitleTranslator.GetAvailableModels(data.get('api_key'), data.get('api_base'))

        self.source_prompt = self.data.get('gpt_prompt')
        self.source_instructions = self.data.get('instructions')

        self.form_layout = QFormLayout()
        self.model_edit = self._add_form_option("model", self.data.get('gpt_model', ''), self.models, tooltip="Model to use for translation")
        self.prompt_edit = self._add_form_option("prompt", self.data.get('gpt_prompt', ''), str, "Prompt for each user translation request")
        self.instructions_edit = self._add_form_option("instructions", self.data.get('instructions', ''), MULTILINE_OPTION, "System instructions for the translator")

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
        self.data['gpt_model'] = self.model_edit.GetValue()
        self.data['gpt_prompt'] = self.prompt_edit.GetValue()
        self.data['instructions'] = self.instructions_edit.GetValue()

        self._check_for_edited_instructions()

        super().accept()

    def reject(self):
        super().reject()

    def _check_for_edited_instructions(self):
        if self.data['instructions'] != self.source_instructions:
            self.data['instruction_file'] = ""
            self.data['instructions_edited'] = True
        if self.data['gpt_prompt'] != self.source_prompt:
            self.data['instructions_edited'] = True

    @property
    def load_icon(self):
        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)
    
    @property
    def save_icon(self):
        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
    
    def _load_instructions(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Instructions", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, "r", encoding='utf-8') as file:
                    content = file.read()
                    self.instructions_edit.SetValue(content)

                self.source_instructions = content
                self.data['instruction_file'] = file_name

            except Exception as e:
                logging.error(f"Unable to read instruction file: {str(e)}")

    def _save_instructions(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Instructions", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            content = self.instructions_edit.GetValue()
            try:
                if not file_name.endswith('.txt'):
                    file_name += '.txt'
                with open(file_name, "w", encoding='utf-8') as file:
                    file.write(content)

                self.source_instructions = content
                self.data['instruction_file'] = file_name

            except Exception as e:
                logging.error(f"Unable to write instruction file: {str(e)}")

    def set_defaults(self):
        options = Options()
        self.model_edit.SetValue(options.get('gpt_model'))
        self.prompt_edit.SetValue(options.get('gpt_prompt'))
        self.instructions_edit.SetValue(options.get('instructions'))
        self.data['instruction_file'] = options.get('instruction_file')
