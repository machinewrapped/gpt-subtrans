from PySide6.QtWidgets import QStyle, QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption

class TranslatorOptionsDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Translator Options")

        self.data = data

        layout = QVBoxLayout()

        self.model_label = QLabel("Model")
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("Enter Model")
        self.model_edit.setText(self.data.get('gpt_model', ''))

        self.prompt_label = QLabel("Prompt")
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText("Enter Prompt")
        self.prompt_edit.setText(self.data.get('gpt_prompt', ''))

        self.instructions_label = QLabel("Instructions")
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText("Enter Instructions")
        self.instructions_edit.setPlainText(self.data.get('instructions', ''))
        self.instructions_edit.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)

        self.load_button = QPushButton(self.load_icon, "Load Instructions")
        self.load_button.clicked.connect(self._load_instructions)

        self.save_button = QPushButton(self.save_icon, "Save Instructions")
        self.save_button.clicked.connect(self._save_instructions)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        layout.addWidget(self.model_label)
        layout.addWidget(self.model_edit)
        layout.addWidget(self.prompt_label)
        layout.addWidget(self.prompt_edit)
        layout.addWidget(self.instructions_label)
        layout.addWidget(self.instructions_edit)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

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

    def accept(self):
        self.data['gpt_model'] = self.model_edit.text()
        self.data['gpt_prompt'] = self.prompt_edit.text()
        self.data['instructions'] = self.instructions_edit.toPlainText()
        super().accept()

    def reject(self):
        super().reject()
