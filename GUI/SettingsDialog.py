import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QDialogButtonBox, QWidget, QFormLayout, QFrame)
from GUI.GuiHelpers import GetInstructionFiles, GetThemeNames

from GUI.Widgets.OptionsWidgets import CreateOptionWidget
from PySubtitle.SubtitleTranslator import SubtitleTranslator

class SettingsDialog(QDialog):
    SECTIONS = {
        'General': {
            'theme': [],
            'autosave': bool,
            'write_backup': bool,
            'stop_on_error': bool,
            'max_threads': (int, "Maximum number of simultaneous translation threads for fast translation")
        },
        'GPT': {
            'api_key': (str, "An OpenAI API key is required to use this program (https://platform.openai.com/account/api-keys)"),
            'api_base': (str, "The base URI to use for requests - leave as default unless you know you need something else"),
            'gpt_model': str,
            'temperature': (float, "Amount of random variance to add to translations. Generally speaking, none is best"),
            'rate_limit': (float, "Maximum OpenAI API requests per minute. Mainly useful if you are on the restricted free plan"),
            'max_instruct_tokens': (int, "Maximum tokens a completion can contain (only applicable for -instruct models)")
        },
        'Translation': {
            'gpt_prompt': (str, "The (brief) instruction to give GPT for each batch of subtitles. [movie_name] and [to_language] are automatically filled in"),
            'target_language': str,
            'include_original': (bool, "Include original text in translated subtitles"),
            'instruction_file': (str, "Detailed instructions for GPT about how to approach translation, and the required response format"),
            'allow_retranslations': (bool, "If true, translations that fail validation will be sent to GPT again with a note to allow it to correct the mistake"),
            'enforce_line_parity': (bool, "Validator: If true, require one translated line for each source line")
        },
        'Advanced': {
            'min_batch_size': (int, "Avoid creating a new batch smaller than this"),
            'max_batch_size': (int, "Divide any batches larger than this into multiple batches"),
            'scene_threshold': (float, "Consider a new scene to have started after this many seconds without subtitles"),
            'batch_threshold': (float, "Consider starting a new batch after a gap of this many seconds (simple batcher only)"),
            'use_simple_batcher': (bool, "Use old batcher instead of batching dynamically based on gap size"),
            'match_partial_words': (bool, "Used with substitutions, required for some languages where word boundaries aren't detected"),
            'whitespaces_to_newline': (bool, "Convert blocks of whitespace and Chinese Commas to newlines"),
            'max_context_summaries': (int, "Limits the number of scene/batch summaries to include as context with each translation batch"),
            'max_characters': (int, "Validator: Maximum number of characters to allow in a single translated line"),
            'max_newlines': (int, "Validator: Maximum number of newlines to allow in a single translated line"),
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

        models = SubtitleTranslator.GetAvailableModels(options.get('api_key'), options.get('api_base'))
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
            key_type, tooltip = key_type if isinstance(key_type, tuple) else (key_type, None)
            field = CreateOptionWidget(key, self.options[key], key_type, tooltip=tooltip)
            layout.addRow(field.name, field)

        return section_widget

    def accept(self):
        try:
            for section_name in self.SECTIONS.keys():
                section_widget = self.sections.findChild(QWidget, section_name)

                if section_widget is None:
                    logging.warning(f"No widget found for section {section_name}")
                    continue

                layout = section_widget.layout()
                if layout is None:
                    logging.warning(f"No layout found for section {section_name}")
                    continue

                for row in range(layout.rowCount()):
                    field = layout.itemAt(row, QFormLayout.FieldRole).widget()
                    self.options[field.key] = field.GetValue()

        except Exception as e:
            logging.error(f"Unable to update settings: {e}")

        try:
            super(SettingsDialog, self).accept()

        except Exception as e:
            logging.error(f"Error in settings dialog handler: {e}")
            self.reject()

    def reject(self):
        super(SettingsDialog, self).reject()
