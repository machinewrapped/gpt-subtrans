import os
from PySide6.QtWidgets import (
    QFormLayout, 
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QLineEdit, 
    QTextEdit, 
    QPushButton, 
    QCheckBox, 
    QDoubleSpinBox, 
    QComboBox,
    QSpinBox 
    )
from PySide6.QtGui import QTextOption

from PySubtitleGPT.Helpers import GetResourcePath


class FirstRunOptions(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("First Run Options")
        self.setMinimumWidth(600)

        self.data = data

        layout = QVBoxLayout()

        self.form_layout = QFormLayout()

        api_key = self.data.get('api_key', '')
        self.api_key = self._create_input("API Key", QLineEdit, "Enter API Key", api_key)
        self.api_key.textChanged.connect(self._api_key_changed)

        self.language = self._create_input("Language", QLineEdit, "Target Language", self.data.get('target_language', ''))

        self.theme_path = GetResourcePath("theme")
        self.theme = self._add_theme_input("Theme", self.data.get('theme', 'default'))

        self.model = self._create_input("Model", QLineEdit, "Default Model", self.data.get('gpt_model', ''))

        self.free_plan = self._create_input("OpenAI Free Plan", QCheckBox, default_value=self.data.get('rate_limit', False) and True)

        self.max_threads = self._create_input("Max Threads", QSpinBox, default_value=self.data.get('max_threads', 1))
        self.max_threads.setRange(1, 16)

        self.rate_limit = self._create_input("Rate Limit", QSpinBox, default_value=self.data.get('rate_limit', None))
        self.rate_limit.setRange(0, 999)

        layout.addLayout(self.form_layout)

        self.button_layout = QHBoxLayout()

        self.ok_button = self._create_button("OK", self.accept)
        self.ok_button.setEnabled(api_key and True)

        layout.addLayout(self.button_layout)

        self.setLayout(layout)

        self.free_plan.stateChanged.connect(self._on_free_plan_changed)

    def accept(self):
        self.data['api_key'] = self.api_key.text()
        self.data['gpt_model'] = self.model.text()
        self.data['target_language'] = self.language.text()
        self.data['max_threads'] = self.max_threads.value()
        self.data['rate_limit'] = self.rate_limit.value()
        self.data['theme'] = self.theme.currentText()
        super().accept()

    def _create_input(self, label_text, input_type, placeholder=None, default_value=None):
        label = QLabel(label_text)
        input_widget = input_type()

        if placeholder:
            input_widget.setPlaceholderText(placeholder)

        if default_value is not None:
            if isinstance(input_widget, QLineEdit) or isinstance(input_widget, QTextOption):
                input_widget.setText(default_value)
            elif isinstance(input_widget, QSpinBox):
                input_widget.setValue(int(default_value))
            elif isinstance(input_widget, QDoubleSpinBox):
                input_widget.setValue(float(default_value))
            elif isinstance(input_widget, QCheckBox):
                input_widget.setChecked(default_value)

        self.form_layout.addRow(label, input_widget)
        return input_widget

    def _create_button(self, text, on_click):
        button = QPushButton(text)
        button.clicked.connect(on_click)
        self.button_layout.addWidget(button)
        return button
    
    def _api_key_changed(self, text):
        self.ok_button.setEnabled(text != "")

    def _on_free_plan_changed(self, state):
        if state:
            self.max_threads.setValue(1)
            self.rate_limit.setValue(5)
            self.max_threads.setEnabled(False)
            self.rate_limit.setEnabled(False)
        else:
            self.max_threads.setValue(self.data.get('max_threads', 1))
            self.rate_limit.setValue(self.data.get('rate_limit', None))
            self.max_threads.setEnabled(True)
            self.rate_limit.setEnabled(False)

    def _add_theme_input(self, label_text, current_theme):
        theme = QComboBox()
        theme.addItem('default')
        for file in os.listdir(self.theme_path):
            if file.endswith(".qss"):
                theme_name = os.path.splitext(file)[0]
                theme.addItem(theme_name)

        if current_theme is None:
            theme.setCurrentIndex(0)
        else:
            index = theme.findText(current_theme)
            if index != -1:
                theme.setCurrentIndex(index)

        self.form_layout.addRow(label_text, theme)

        return theme

