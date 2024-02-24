import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QDialogButtonBox, QWidget, QFormLayout, QFrame)
from GUI.GuiHelpers import ClearForm, GetInstructionFiles, GetThemeNames, LoadInstructionsResource

from GUI.Widgets.OptionsWidgets import CreateOptionWidget
from PySubtitle.Options import Options
from PySubtitle.TranslationProvider import TranslationProvider

class SettingsDialog(QDialog):
    PROVIDER_SECTION = 'Provider Settings'
    SECTIONS = {
        'General': {
            'target_language': (str, "The default language to translate the subtitles to"),
            'include_original': (bool, "Include original text in translated subtitles"),
            'instruction_file': (str, "Instructions for the translation provider to follow"),
            'prompt': (str, "The (brief) instruction for each batch of subtitles. Some [tags] are automatically filled in"),
            'theme': [],
            'allow_retranslations': (bool, "If true, translations that fail validation will be sent again with a note about the mistake"),
            'enforce_line_parity': (bool, "Validator: If true, require one translated line for each source line"),
            'autosave': (bool, "Automatically save the project after each translation batch"),
            'write_backup': (bool, "Save a backup copy of the project when opening it"),
            'stop_on_error': (bool, "Stop translating if an error is encountered")
        },
        PROVIDER_SECTION: {
            'provider': ([], "The AI translation service to use"),
            'provider_settings': TranslationProvider,
        },
        'Advanced': {
            'max_threads': (int, "Maximum number of simultaneous translation threads for fast translation"),
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
            'max_retries': (int, "Number of times to retry a failed translation before giving up"),
            'backoff_time': (float, "Seconds to wait before retrying a failed translation"),
        }
    }

    def __init__(self, options : Options, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("GUI-Subtrans Settings")
        self.setMinimumWidth(800)

        self.translation_provider : TranslationProvider = None
        self.settings = options.GetSettings()
        self.widgets = {}

        # Qyery available themes
        self.SECTIONS['General']['theme'] = ['default'] + GetThemeNames()

        # Query available instruction files
        instruction_files = GetInstructionFiles()
        if instruction_files:
            self.SECTIONS['General']['instruction_file'] = instruction_files

        # Query available providers
        self.providers = sorted(TranslationProvider.get_providers())
        self.SECTIONS[self.PROVIDER_SECTION]['provider'] = (self.providers, self.SECTIONS[self.PROVIDER_SECTION]['provider'][1])

        # Initialise the current translation provider
        self._initialise_translation_provider()

        # Initalise the tabs
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs)
        self.sections = {}

        for section_name in self.SECTIONS.keys():
            section_widget = self._create_section_widget(section_name)
            self.tabs.addTab(section_widget, section_name)

        # Add Ok and Cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

    @property
    def provider_settings(self):
        return self.settings.get('provider_settings', {})

    def accept(self):
        try:
            for section_name in self.SECTIONS.keys():
                section_widget = self.tabs.findChild(QWidget, section_name)
                layout = section_widget.layout()

                for row in range(layout.rowCount()):
                    field = layout.itemAt(row, QFormLayout.FieldRole).widget()
                    self.settings[field.key] = field.GetValue()
            
            # Update the provider settings
            options = Options(self.settings)
            if options.provider:
                TranslationProvider.update_provider_settings(options)            

        except Exception as e:
            logging.error(f"Unable to update settings: {e}")

        try:
            super(SettingsDialog, self).accept()

        except Exception as e:
            logging.error(f"Error in settings dialog handler: {e}")
            self.reject()

    def reject(self):
        super(SettingsDialog, self).reject()

    def _create_section_widget(self, section_name):
        section_widget = QFrame(self)
        section_widget.setObjectName(section_name)

        layout = QFormLayout(section_widget)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self._populate_form(section_name, layout)

        self.sections[section_name] = section_widget

        return section_widget

    def _populate_form(self, section_name : str, layout : QFormLayout):
        """
        Create the form fields for the options 
        """
        ClearForm(layout)

        options = self.SECTIONS[section_name]

        for key, key_type in options.items():
            key_type, tooltip = key_type if isinstance(key_type, tuple) else (key_type, None)
            if key_type == TranslationProvider:
                self._add_provider_options(section_name, layout)
            else:
                field = CreateOptionWidget(key, self.settings[key], key_type, tooltip=tooltip)
                field.contentChanged.connect(lambda setting=field: self._on_setting_changed(section_name, setting.key, setting.GetValue()))
                layout.addRow(field.name, field)
                self.widgets[key] = field

    def _initialise_translation_provider(self):
        """
        Initialise translation provider
        """
        provider = self.settings.get('provider')
        if provider:
            provider_settings = self.provider_settings.get(provider, {})
            self.translation_provider : TranslationProvider = TranslationProvider.create_provider(provider, provider_settings)

    def _add_provider_options(self, section_name : str, layout : QFormLayout):
        """
        Add the options for a translation provider to a form
        """
        if not self.translation_provider:
            logging.warning("Translation provider is not configured")
            return

        provider_options = self.translation_provider.GetOptions()
        provider_settings = self.provider_settings.get(self.translation_provider.name, {})

        for key, key_type in provider_options.items():
            key_type, tooltip = key_type if isinstance(key_type, tuple) else (key_type, None)
            field = CreateOptionWidget(key, provider_settings.get(key), key_type, tooltip=tooltip)
            field.contentChanged.connect(lambda setting=field: self._on_setting_changed(section_name, setting.key, setting.GetValue()))
            layout.addRow(field.name, field)
            self.widgets[key] = field

    def _refresh_provider_options(self):
        """
        Populate the provider-specific options
        """
        if not self.translation_provider:
            logging.warning("Translation provider is not configured")
            return
        
        provider_settings = self.provider_settings.get(self.translation_provider.name, {})
        self.translation_provider.settings.update(provider_settings)

        section_name = self.PROVIDER_SECTION
        section_widget = self.sections.get(section_name)
        if section_widget:
            section_layout = section_widget.layout()
            self._populate_form(section_name, section_layout)

    def _on_setting_changed(self, section_name, key, value):
        """
        Update the settings when a field is changed
        """
        self.settings[key] = value

        if key == 'provider':
            self._initialise_translation_provider()
            self._refresh_provider_options()

        elif key == 'instruction_file':
            self._update_instruction_file()

        elif section_name == self.PROVIDER_SECTION:
            provider = self.settings.get('provider')
            provider_settings = self.provider_settings.get(provider, {})
            provider_settings[key] = value

            # TODO: Ask the provider class for a list of settings that should trigger a refresh
            if key in ['api_key', 'api_base', 'model']:
                self._refresh_provider_options()

    def _update_instruction_file(self):
        """
        Update the prompt when the instruction file is changed
        """
        instruction_file = self.widgets['instruction_file'].GetValue()
        if instruction_file:
            try:
                instructions = LoadInstructionsResource(instruction_file)
                self.widgets['prompt'].SetValue(instructions.prompt)
            except Exception as e:
                logging.error(f"Unable to load instructions from {instruction_file}: {e}")
    

