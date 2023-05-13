from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QDialogButtonBox, QWidget, QFormLayout, QSizePolicy, QFrame)

from GUI.Widgets.OptionsWidgets import CreateDropdownOptionWidget, CreateOptionWidget

class SettingsDialog(QDialog):
    SECTIONS = {
        'General': ['theme', 'write_backup', 'stop_on_error'], 
        'GPT': ['api_key', 'gpt_model', 'gpt_prompt', 'temperature', 'rate_limit', 'max_retries'],
        'Translation': ['target_language', 'allow_retranslations', 'enforce_line_parity', 'max_context_summaries', 'max_characters', 'max_newlines'],
        'Advanced': ['scene_threshold', 'batch_threshold', 'min_batch_size', 'max_batch_size']
    }

    DROPDOWNS = {
        'theme': ['subtrans', 'subtrans-dark']
    }

    def __init__(self, options, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("GUI-Subtrans Settings")
        self.setMinimumWidth(800)

        self.options = options

        self.layout = QVBoxLayout(self)

        self.sections = QTabWidget(self)
        self.layout.addWidget(self.sections)

        for section_name, keys in self.SECTIONS.items():
            section_widget = self.create_section_widget(keys, section_name)
            self.sections.addTab(section_widget, section_name)

        # Add Ok and Cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

    def create_section_widget(self, keys, section_name):
        section_widget = QFrame(self)
        section_widget.setObjectName(section_name)

        layout = QFormLayout(section_widget)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        for key in keys:
            if key in self.DROPDOWNS:
                field = CreateDropdownOptionWidget(key, self.DROPDOWNS[key], self.options[key])
            else:
                field = CreateOptionWidget(key, self.options[key])
            
            layout.addRow(field.name, field)

        return section_widget

    def accept(self):
        for section_name in self.SECTIONS.keys():
            section_widget = self.sections.findChild(QWidget, section_name)
            layout = section_widget.layout()

            for row in range(layout.rowCount()):
                field = layout.itemAt(row, QFormLayout.FieldRole).widget()
                self.options[field.key] = field.get_value()

        super(SettingsDialog, self).accept()

    def reject(self):
        super(SettingsDialog, self).reject()
