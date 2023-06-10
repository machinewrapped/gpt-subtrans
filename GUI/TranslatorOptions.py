from PySide6.QtWidgets import (
    QStyle, 
    QApplication, 
    QFormLayout, 
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QLineEdit, 
    QTextEdit, 
    QPushButton, 
    QFileDialog, 
    QDoubleSpinBox, 
    QSpinBox 
    )
from PySide6.QtGui import QTextOption

from PySubtitleGPT.Options import Options

class TranslatorOptionsDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Translator Options")
        self.setMinimumWidth(800)

        self.data = data

        layout = QVBoxLayout()

        self.form_layout = QFormLayout()

        self.model_edit = self._create_input("Model", QLineEdit, "Enter Model", self.data.get('gpt_model', ''))

        self.prompt_edit = self._create_input("Prompt", QLineEdit, "Enter Prompt", self.data.get('gpt_prompt', ''))

        self.instructions_edit = self._create_input("Instructions", QTextEdit, "Enter Instructions", self.data.get('instructions', ''), QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

        layout.addLayout(self.form_layout)

        self.button_layout = QHBoxLayout()

        self.load_button = self._create_button("Load Instructions", self._load_instructions)
        self.save_button = self._create_button("Save Instructions", self._save_instructions)
        self.default_button = self._create_button("Defaults", self.set_defaults)
        self.ok_button = self._create_button("OK", self.accept)
        self.cancel_button = self._create_button("Cancel", self.reject)

        layout.addLayout(self.button_layout)

        self.setLayout(layout)

    def _create_input(self, label_text, input_type, placeholder=None, default_value=None, word_wrap_mode=None):
        label = QLabel(label_text)
        input_widget = input_type()

        if placeholder:
            input_widget.setPlaceholderText(placeholder)

        if default_value is not None:
            if isinstance(input_widget, QLineEdit):
                input_widget.setText(default_value)
            elif isinstance(input_widget, QTextEdit):
                input_widget.setPlainText(default_value)
                input_widget.setWordWrapMode(word_wrap_mode)
            elif isinstance(input_widget, QSpinBox) or isinstance(input_widget, QDoubleSpinBox):
                input_widget.setValue(default_value)

        self.form_layout.addRow(label, input_widget)
        return input_widget

    def _create_button(self, text, on_click):
        button = QPushButton(text)
        button.clicked.connect(on_click)
        self.button_layout.addWidget(button)
        return button

    def accept(self):
        self.data['gpt_model'] = self.model_edit.text()
        self.data['gpt_prompt'] = self.prompt_edit.text()
        self.data['instructions'] = self.instructions_edit.toPlainText()
        super().accept()


    def reject(self):
        super().reject()

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
            with open(file_name, "r") as file:
                content = file.read()
                self.instructions_edit.setPlainText(content)

    def _save_instructions(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Instructions", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            if not file_name.endswith('.txt'):
                file_name += '.txt'
            with open(file_name, "w") as file:
                content = self.instructions_edit.toPlainText()
                file.write(content)

    def set_defaults(self):
        options = Options()
        self.model_edit.setText(options.get('gpt_model'))
        self.prompt_edit.setText(options.get('gpt_prompt'))
        self.instructions_edit.setPlainText(options.get('instructions'))