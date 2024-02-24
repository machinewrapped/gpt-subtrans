from PySide6.QtWidgets import (
    QFormLayout, 
    QDialog, 
    QVBoxLayout, 
    QDialogButtonBox,
    QFrame,
    QMessageBox 
    )

from GUI.GuiHelpers import GetThemeNames
from GUI.Widgets.OptionsWidgets import CreateOptionWidget, OptionWidget, TextOptionWidget
from PySubtitle.Options import Options
from PySubtitle.TranslationProvider import TranslationProvider

class FirstRunOptions(QDialog):
    OPTIONS = {
        'target_language': (str, "Default language to translate the subtitles to"),
        'theme': ([], "Customise the appearance of gui-subtrans"),
        'provider': ([], "The translation provider to use"),
        'api_key': (str, "An API Key is required to use this provider"),
        'api_base': (str, "Base URL for the provider (if unsure, do not change)"),
        'model': ([], "AI model to use as the translator"),
        'free_plan': (bool, "Select this if your OpenAI API Key is for a trial version")
    }

    GLOBAL_SETTINGS = ['provider', 'target_language', 'theme']

    def __init__(self, options : Options, parent=None):
        super().__init__(parent)
        self.setWindowTitle("First Run Options")
        self.setMinimumWidth(600)

        self.options = Options(options)

        if not options.provider:
            options.provider = "OpenAI"

        self.providers = sorted(TranslationProvider.get_providers())
        self.OPTIONS['provider'] = (self.providers, self.OPTIONS['provider'][1])

        available_models = TranslationProvider.get_available_models(options)
        self.OPTIONS['model'] = (available_models, self.OPTIONS['model'][1])

        self.OPTIONS['theme'] = (['default'] + GetThemeNames(), self.OPTIONS['theme'][1])

        self.controls = {}

        settings_widget = QFrame(self)

        self.form_layout = QFormLayout(settings_widget)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        for key, setting in self.OPTIONS.items():
            key_type, tooltip = setting
            field : OptionWidget = CreateOptionWidget(key, options.get(key), key_type, tooltip=tooltip)
            self.form_layout.addRow(field.name, field)
            self.controls[key] = field

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(settings_widget)

        self.provider_edit : OptionWidget = self.controls.get('provider')
        self.model_edit : OptionWidget = self.controls.get('model')
        self.api_key_edit : TextOptionWidget = self.controls.get('api_key')
        self.api_base_edit : TextOptionWidget = self.controls.get('api_base')

        self._update_provider_settings()
        self._get_provider_settings()

        self.provider_edit.contentChanged.connect(self._provider_changed)
        self.api_key_edit.contentChanged.connect(self._update_provider_settings)
        self.api_base_edit.contentChanged.connect(self._update_provider_settings)

        # Add Ok and Cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.buttonBox.accepted.connect(self.accept)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

    def accept(self):
        self._update_provider_settings()

        provider_class : TranslationProvider = TranslationProvider.get_provider(self.options)

        if provider_class.ValidateSettings():
            super().accept()
        else:
            QMessageBox.warning(self, "Missing Information", provider_class.validation_message, QMessageBox.StandardButton.Ok)

    def GetSettings(self):
        return self.options.GetSettings()

    def _provider_changed(self):
        """ Reload the settings for the selected provider """
        self.options['provider'] = self.provider_edit.GetValue()
        self._get_provider_settings()
        self._update_provider_settings()

    def _get_provider_settings(self):
        """ Get the settings for the selected provider and disable the settings that are not available """
        provider_class : TranslationProvider = TranslationProvider.get_provider(self.options)

        if provider_class:
            for key, value in provider_class.settings.items():
                self.options.add(key, value)

            for key, control in self.controls.items():
                has_setting = key in provider_class.settings or key in self.GLOBAL_SETTINGS
                control.SetEnabled(has_setting)
                if has_setting:
                    control.SetValue(self.options.get(key))

    def _update_provider_settings(self):
        """ Update the settings for the selected provider """
        for row in range(self.form_layout.rowCount()):
            field = self.form_layout.itemAt(row, QFormLayout.FieldRole).widget()
            value = field.GetValue()
            if value:
                self.options.add(field.key, value)

        TranslationProvider.update_provider_settings(self.options)

        available_models = TranslationProvider.get_available_models(self.options)
        if available_models:
            self.model_edit.SetOptions(available_models, self.options.get('model'))

