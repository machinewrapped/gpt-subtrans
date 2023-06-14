import json
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit, QSizePolicy, QHBoxLayout, QVBoxLayout)

MULTILINE_OPTION = 'multiline'

class OptionWidget(QWidget):
    def __init__(self, key, initial_value, parent=None):
        super(OptionWidget, self).__init__(parent)
        self.key = key
        self.name = self.GenerateName(key)
        self.initial_value = initial_value
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    @staticmethod
    def GenerateName(key):
        return key.replace('_', ' ').title()

    def GetValue(self):
        raise NotImplementedError

class TextOptionWidget(OptionWidget):
    def __init__(self, key, initial_value):
        super(TextOptionWidget, self).__init__(key, initial_value)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.text_field = QLineEdit(self)
        self.text_field.setText(initial_value)
        self.text_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.layout.addWidget(self.text_field)

    def GetValue(self):
        return self.text_field.text()

class MultilineTextOptionWidget(OptionWidget):
    def __init__(self, key, initial_value):
        super(MultilineTextOptionWidget, self).__init__(key, initial_value)
        content = self._get_content(initial_value)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.text_field = QTextEdit(self)
        self.text_field.setAcceptRichText(False)
        self.text_field.setPlainText(content)
        self.text_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.layout.addWidget(self.text_field)

    def GetValue(self):
        return self.text_field.toPlainText()
    
    def SetReadOnly(self, is_read_only : bool):
        self.text_field.setReadOnly(is_read_only)

    def _get_content(self, value):
        """
        Convert a value to a human-readable string
        """
        if isinstance(value, str):
            return value.replace('\\n', '\n')
        elif isinstance(value, list):
            return '\n'.join(self._get_content(x) for x in value)
        elif isinstance(value, dict):
            jsonstring = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=self._encode_content)
            return self._get_content(jsonstring)
        elif isinstance(value, (int, float)):
            return f'{value:,}'  # Format number with commas
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')  # Format date
        elif value is None:
            return ''  # Return empty string for None
        else:
            return str(value)

    def _encode_content(obj):
        return str(obj)

class IntegerOptionWidget(OptionWidget):
    def __init__(self, key, initial_value):
        super(IntegerOptionWidget, self).__init__(key, initial_value)
        self.spin_box = QSpinBox(self)
        self.spin_box.setMaximum(9999)
        self.spin_box.setMinimumWidth(100)
        self.spin_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        if initial_value:
            self.spin_box.setValue(initial_value)

    def GetValue(self):
        return self.spin_box.value()

class FloatOptionWidget(OptionWidget):
    def __init__(self, key, initial_value):
        super(FloatOptionWidget, self).__init__(key, initial_value)
        self.double_spin_box = QDoubleSpinBox(self)
        self.double_spin_box.setMaximum(9999.99)
        self.double_spin_box.setMinimumWidth(100)
        self.double_spin_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        if initial_value:
            self.double_spin_box.setValue(initial_value)

    def GetValue(self):
        return self.double_spin_box.value()

class CheckboxOptionWidget(OptionWidget):
    def __init__(self, key, initial_value):
        super(CheckboxOptionWidget, self).__init__(key, initial_value)
        self.check_box = QCheckBox(self)
        if initial_value:
            self.check_box.setChecked(initial_value)

    def GetValue(self):
        return self.check_box.isChecked()

class DropdownOptionWidget(OptionWidget):
    def __init__(self, key, values, initial_value):
        super(DropdownOptionWidget, self).__init__(key, initial_value)
        self.combo_box = QComboBox(self)
        for value in values:
            self.combo_box.addItem(value)

        if initial_value:
            self.combo_box.setCurrentIndex(self.combo_box.findText(initial_value))

    def GetValue(self):
        return self.combo_box.currentText()

def CreateOptionWidget(key, initial_value, key_type):
    # Helper function to create an OptionWidget based on the specified type
    if isinstance(key_type, list):
        return DropdownOptionWidget(key, key_type, initial_value)
    elif key_type == MULTILINE_OPTION:
        return MultilineTextOptionWidget(key, initial_value)
    elif key_type == str:
        return TextOptionWidget(key, initial_value)
    elif key_type == int:
        return IntegerOptionWidget(key, initial_value)
    elif key_type == float:
        return FloatOptionWidget(key, initial_value)
    elif key_type == bool:
        return CheckboxOptionWidget(key, initial_value)
    else:
        raise ValueError('Unsupported option type: ' + str(type(initial_value)))
