from PySide6.QtWidgets import (
    QFormLayout, 
    QDialog, 
    QVBoxLayout, 
    QDialogButtonBox,
    QFrame,
    QMessageBox 
    )

from GUI.GuiHelpers import GetThemeNames
from GUI.Widgets.OptionsWidgets import CreateOptionWidget, CheckboxOptionWidget, IntegerOptionWidget, OptionWidget, TextOptionWidget
from PySubtitle.SubtitleTranslator import SubtitleTranslator


class FirstRunOptions(QDialog):
    SETTINGS = {
        'api_key': (str, "An OpenAI API Key is required to use this program"),
        'api_base': (str, "Base URL for OpenAI API calls (if unsure, do not change)"),
        'model': ([], "AI model to use as the translator"),
        'target_language': (str, "Default language to translate the subtitles to"),
        'theme': ([], "Customise the appearance of gui-subtrans"),
        'free_plan': (bool, "Select this if your OpenAI API Key is for a trial version"),
        'max_threads': (int, "Maximum simultaneous translation threads"),
        'rate_limit': (int, "Rate-limit OpenAI API requests per minute (heavily restricted on trial plans)")
    }

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("First Run Options")
        self.setMinimumWidth(600)

        on_free_plan = 'rate_limit' in data and (data.get('rate_limit') or 0.0) > 0.0
        data['free_plan'] = on_free_plan

        self.data = data

        models = SubtitleTranslator.GetAvailableModels(self.data)
        self.SETTINGS['model'] = (models, self.SETTINGS['model'][1])

        self.SETTINGS['theme'] = (['default'] + GetThemeNames(), self.SETTINGS['theme'][1])

        self.controls = {}

        settings_widget = QFrame(self)

        self.form_layout = QFormLayout(settings_widget)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        for key, setting in self.SETTINGS.items():
            key_type, tooltip = setting
            field : OptionWidget = CreateOptionWidget(key, self.data[key], key_type, tooltip=tooltip)
            self.form_layout.addRow(field.name, field)
            self.controls[key] = field

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(settings_widget)

        self.model_edit : OptionWidget = self.controls.get('model')

        self.api_key_edit : TextOptionWidget = self.controls.get('api_key')
        self.api_key_edit.contentChanged.connect(self._update_models)

        self.api_base_edit : TextOptionWidget = self.controls.get('api_base')
        self.api_base_edit.contentChanged.connect(self._update_models)

        self.free_plan_edit : CheckboxOptionWidget = self.controls.get('free_plan')
        if self.free_plan_edit:
            self.free_plan_edit.SetValue(on_free_plan)
            self.free_plan_edit.contentChanged.connect(self._on_free_plan_changed)

        self.max_threads_edit : IntegerOptionWidget = self.controls.get('max_threads')
        if self.max_threads_edit:
            self.max_threads_edit.SetRange(1, 16)

        self.rate_limit_edit : IntegerOptionWidget = self.controls.get('rate_limit')
        if self.rate_limit_edit:
            self.rate_limit_edit.SetRange(0, 999)

        # Add Ok and Cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.buttonBox.accepted.connect(self.accept)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

        self._on_free_plan_changed()

    def accept(self):
        key = self.api_key_edit.GetValue()
        if key:
            for row in range(self.form_layout.rowCount()):
                field = self.form_layout.itemAt(row, QFormLayout.FieldRole).widget()
                self.data[field.key] = field.GetValue()

            super().accept()
        else:
            QMessageBox.warning(self, "API Key Required", "You must provide an OpenAI API Key.")

    def _on_free_plan_changed(self):
        is_free_plan = self.free_plan_edit.GetValue()
        if is_free_plan:
            self.max_threads_edit.SetValue(1)
            self.max_threads_edit.SetEnabled(False)

            self.rate_limit_edit.SetValue(5)
            self.rate_limit_edit.SetEnabled(True)
        else:
            max_threads = self.data.get('max_threads') or 4
            self.max_threads_edit.SetValue(max_threads)
            self.max_threads_edit.SetEnabled(True)

            rate_limit = self.data.get('rate_limit') or 0.0
            self.rate_limit_edit.SetValue(rate_limit)

    def _update_models(self):
        self.data['api_key'] = self.api_key_edit.GetValue()
        self.data['api_base'] = self.api_base_edit.GetValue()
        if self.data['api_key'] and self.data['api_base']:
            models = SubtitleTranslator.GetAvailableModels(self.data)
            self.model_edit.SetOptions(models, self.data.get('model'))
            self.model_edit.SetValue(models[0])
