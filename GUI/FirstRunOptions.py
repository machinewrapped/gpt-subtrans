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
        'provider': ([], "The translation provider to use"),
        'theme': ([], "Customise the appearance of gui-subtrans")
    }

    def __init__(self, options : Options, parent=None):
        super().__init__(parent)
        self.setWindowTitle("First Run Options")
        self.setMinimumWidth(600)

        self.options = Options(options)

        if not options.provider:
            options.provider = "OpenAI"

        self.providers = sorted(TranslationProvider.get_providers())
        self.OPTIONS['provider'] = (self.providers, self.OPTIONS['provider'][1])

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

        # Add Ok and Cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.buttonBox.accepted.connect(self.accept)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

    def accept(self):
        """ Update the settings """
        for row in range(self.form_layout.rowCount()):
            field = self.form_layout.itemAt(row, QFormLayout.FieldRole).widget()
            value = field.GetValue()
            if value:
                self.options.add(field.key, value)
        
        super().accept()

    def GetSettings(self):
        return self.options.GetSettings()

