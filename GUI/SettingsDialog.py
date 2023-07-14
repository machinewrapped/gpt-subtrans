from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QDialogButtonBox, QWidget, QFormLayout, QFrame)
from GUI.GuiHelpers import GetInstructionFiles, GetThemeNames

from GUI.Widgets.OptionsWidgets import CreateOptionWidget
from PySubtitleGPT.SubtitleTranslator import SubtitleTranslator

class SettingsDialog(QDialog):
    SECTIONS = {
        'General': {
            'theme': [],
            'autosave': bool,
            'write_backup': bool,
            'stop_on_error': bool,
            'max_threads': int
        },
        'GPT': {
            'api_key': str,
            'api_base': str,
            'gpt_model': str,
            'temperature': float,
            'rate_limit': float
        },
        'Translation': {
            'gpt_prompt': str,
            'target_language': str,
            'instruction_file': str,
            'allow_retranslations': bool,
            'enforce_line_parity': bool
        },
        'Advanced': {
            'min_batch_size': int,
            'max_batch_size': int,
            'scene_threshold': float,
            'batch_threshold': float,
            'match_partial_words': bool,
            'whitespaces_to_newline': bool,
            'max_context_summaries': int,
            'max_characters': int,
            'max_newlines': int,
            'max_retries': int,
            'backoff_time': float
        }
    }

    def __init__(self, options, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("GUI-Subtrans Settings")
        self.setMinimumWidth(800)

        self.options = options

        self.SECTIONS['General']['theme'] = ['default'] + GetThemeNames()

        models = SubtitleTranslator.GetAvailableModels(options.get('api_key'))
        if models:
            self.SECTIONS['GPT']['gpt_model'] = models

        instruction_files = GetInstructionFiles()
        if instruction_files:
            self.SECTIONS['Translation']['instruction_file'] = instruction_files

        self.layout = QVBoxLayout(self)

        self.sections = QTabWidget(self)
        self.layout.addWidget(self.sections)

        for section_name, settings in self.SECTIONS.items():
            section_widget = self.create_section_widget(settings, section_name)
            self.sections.addTab(section_widget, section_name)

        # Add Ok and Cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

    def create_section_widget(self, settings, section_name):
        section_widget = QFrame(self)
        section_widget.setObjectName(section_name)

        layout = QFormLayout(section_widget)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        for key, key_type in settings.items():
            field = CreateOptionWidget(key, self.options[key], key_type)
            layout.addRow(field.name, field)

        return section_widget

    def accept(self):
        for section_name in self.SECTIONS.keys():
            section_widget = self.sections.findChild(QWidget, section_name)
            layout = section_widget.layout()

            for row in range(layout.rowCount()):
                field = layout.itemAt(row, QFormLayout.FieldRole).widget()
                self.options[field.key] = field.GetValue()

        super(SettingsDialog, self).accept()

    def reject(self):
        super(SettingsDialog, self).reject()
