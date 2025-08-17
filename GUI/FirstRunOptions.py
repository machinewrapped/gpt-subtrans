from PySide6.QtWidgets import (
    QFormLayout, 
    QDialog, 
    QVBoxLayout, 
    QDialogButtonBox,
    QFrame,
    )

from GUI.GuiHelpers import GetThemeNames
from GUI.Widgets.OptionsWidgets import CreateOptionWidget, OptionWidget
from PySubtitle.Options import Options
from PySubtitle.Helpers.Localization import _, get_locale_display_items
from PySubtitle.Helpers.Resources import GetResourcePath
import os

class FirstRunOptions(QDialog):
    OPTIONS = {
        'ui_language': ([], _("The language of the application interface")),
        'target_language': (str, _("Default language to translate the subtitles to")),
        'provider': ([], _("The translation provider to use")),
        'theme': ([], _("Customise the appearance of gui-subtrans"))
    }

    def __init__(self, options : Options, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("First Run Options"))
        self.setMinimumWidth(600)

        self.options = Options(options)

        # Populate provider list
        self.OPTIONS['provider'] = (options.available_providers, self.OPTIONS['provider'][1])

        # Populate theme list
        self.OPTIONS['theme'] = (['default'] + GetThemeNames(), self.OPTIONS['theme'][1])

        # Populate UI languages from locales folder using the shared helper
        self.OPTIONS['ui_language'] = (get_locale_display_items(), self.OPTIONS['ui_language'][1])

        self.controls = {}

        settings_widget = QFrame(self)

        self.form_layout = QFormLayout(settings_widget)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        settings = self.options.GetSettings()
        settings['provider'] = settings.get('provider') or "OpenAI"
        settings['ui_language'] = settings.get('ui_language') or 'en'

        for key, option in self.OPTIONS.items():
            key_type, tooltip = option
            field : OptionWidget = CreateOptionWidget(key, settings.get(key), key_type, tooltip=tooltip)
            self.form_layout.addRow(field.name, field)
            self.controls[key] = field

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(settings_widget)

        # Add Ok and Cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self)
        self.buttonBox.accepted.connect(self.accept)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

    def accept(self):
        """ Update the settings """
        for row in range(self.form_layout.rowCount()):
            field = self.form_layout.itemAt(row, QFormLayout.ItemRole.FieldRole).widget()
            value = field.GetValue()
            if value:
                self.options.add(field.key, value)
        
        super().accept()

    def GetSettings(self):
        initial_settings = self.options.GetSettings()
        initial_settings['firstrun'] = False
        return initial_settings

