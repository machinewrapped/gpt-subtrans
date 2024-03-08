import json
from datetime import datetime

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit, QSizePolicy, QHBoxLayout, QVBoxLayout)
from PySide6.QtGui import QTextOption

MULTILINE_OPTION = 'multiline'

class OptionWidget(QWidget):
    contentChanged = Signal()

    def __init__(self, key, initial_value, parent=None, tooltip = None):
        super(OptionWidget, self).__init__(parent)
        self.key = key
        self.name = self.GenerateName(key)
        self.initial_value = initial_value
        if tooltip:
            self.setToolTip(tooltip)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    @staticmethod
    def GenerateName(key):
        return key.replace('_', ' ').title()

    def GetValue(self):
        raise NotImplementedError
    
    def SetValue(self, value):
        raise NotImplementedError

class TextOptionWidget(OptionWidget):
    def __init__(self, key, initial_value, tooltip = None):
        super(TextOptionWidget, self).__init__(key, initial_value, tooltip=tooltip)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.text_field = QLineEdit(self)
        self.text_field.setText(initial_value)
        self.text_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.text_field.textChanged.connect(self.contentChanged)
        self.layout.addWidget(self.text_field)

    def GetValue(self):
        return self.text_field.text()

    def SetValue(self, value):
        self.text_field.setText(value)
    
    def SetEnabled(self, enabled : bool):
        self.text_field.setEnabled(enabled)

    def SetVisible(self, is_visible : bool):
        self.text_field.setVisible(is_visible)

class MultilineTextOptionWidget(OptionWidget):
    def __init__(self, key, initial_value, tooltip = None):
        super(MultilineTextOptionWidget, self).__init__(key, initial_value, tooltip=tooltip)
        content = self._get_content(initial_value).strip()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.text_field = QTextEdit(self)
        self.text_field.setAcceptRichText(False)
        self.text_field.setPlainText(content)
        self.text_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.text_field.textChanged.connect(self.contentChanged)
        self.text_field.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.layout.addWidget(self.text_field)

    def GetValue(self):
        return self.text_field.toPlainText()
    
    def SetValue(self, value):
        self.text_field.setPlainText(value)

    def SetReadOnly(self, is_read_only : bool):
        self.text_field.setReadOnly(is_read_only)

    def SetEnabled(self, enabled : bool):
        self.text_field.setEnabled(enabled)

    def SetVisible(self, is_visible : bool):
        self.text_field.setVisible(is_visible)

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

    def _encode_content(self, obj):
        return str(obj)

class IntegerOptionWidget(OptionWidget):
    def __init__(self, key, initial_value, tooltip = None):
        super(IntegerOptionWidget, self).__init__(key, initial_value, tooltip=tooltip)
        self.spin_box = QSpinBox(self)
        self.spin_box.setMaximum(9999)
        self.spin_box.setMinimumWidth(100)
        self.spin_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.spin_box.valueChanged.connect(self.contentChanged)
        if initial_value:
            self.spin_box.setValue(initial_value)

    def GetValue(self):
        return self.spin_box.value()
    
    def SetValue(self, value : int):
        self.spin_box.setValue(value)
    
    def SetRange(self, min : int, max : int):
        self.spin_box.setRange(min, max)

    def SetEnabled(self, enabled : bool):
        self.spin_box.setEnabled(enabled)
    
    def SetVisible(self, is_visible : bool):
        self.spin_box.setVisible(is_visible)

class FloatOptionWidget(OptionWidget):
    def __init__(self, key, initial_value, tooltip = None):
        super(FloatOptionWidget, self).__init__(key, initial_value, tooltip=tooltip)
        self.double_spin_box = QDoubleSpinBox(self)
        self.double_spin_box.setMaximum(9999.99)
        self.double_spin_box.setMinimumWidth(100)
        self.double_spin_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.double_spin_box.valueChanged.connect(self.contentChanged)
        if initial_value:
            self.double_spin_box.setValue(initial_value)

    def GetValue(self):
        return self.double_spin_box.value()

    def SetValue(self, value : float):
        self.double_spin_box.setValue(value)
    
    def SetRange(self, min : float, max : float):
        self.double_spin_box.setRange(min, max)

    def SetEnabled(self, enabled : bool):
        self.double_spin_box.setEnabled(enabled)

    def SetVisible(self, is_visible : bool):
        self.double_spin_box.setVisible(is_visible)

class CheckboxOptionWidget(OptionWidget):
    def __init__(self, key, initial_value, tooltip = None):
        super(CheckboxOptionWidget, self).__init__(key, initial_value, tooltip=tooltip)
        self.check_box = QCheckBox(self)
        self.check_box.stateChanged.connect(self.contentChanged)
        if initial_value:
            self.check_box.setChecked(initial_value)

    def GetValue(self):
        return self.check_box.isChecked()
    
    def SetValue(self, checked : bool):
        self.check_box.setChecked(checked)

    def SetEnabled(self, enabled : bool):
        self.check_box.setEnabled(enabled)

    def SetVisible(self, is_visible : bool):
        self.check_box.setVisible(is_visible)

class DropdownOptionWidget(OptionWidget):
    def __init__(self, key, values, initial_value, tooltip = None):
        super(DropdownOptionWidget, self).__init__(key, initial_value, tooltip=tooltip)
        self.combo_box = QComboBox(self)
        self.combo_box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.SetOptions(values, initial_value)
        self.combo_box.currentTextChanged.connect(self.contentChanged)

    def GetValue(self):
        return self.combo_box.currentText()
    
    def SetValue(self, value):
        self.combo_box.setCurrentIndex(self.combo_box.findText(value))

    def SetOptions(self, values, selected_value = None):
        self.combo_box.clear()
        for value in values:
            self.combo_box.addItem(value)
            if selected_value and value == selected_value:
                self.combo_box.setCurrentIndex(self.combo_box.count() - 1)

        self.combo_box.setEnabled(len(values) > 1)
    
    def SetEnabled(self, enabled : bool):
        self.combo_box.setEnabled(enabled)

    def SetVisible(self, is_visible : bool):
        self.combo_box.setVisible(is_visible)

def CreateOptionWidget(key, initial_value, key_type, tooltip = None) -> OptionWidget:
    # Helper function to create an OptionWidget based on the specified type
    if isinstance(key_type, list):
        return DropdownOptionWidget(key, key_type, initial_value, tooltip=tooltip)
    elif key_type == MULTILINE_OPTION:
        return MultilineTextOptionWidget(key, initial_value, tooltip=tooltip)
    elif key_type == str:
        return TextOptionWidget(key, initial_value, tooltip=tooltip)
    elif key_type == int:
        return IntegerOptionWidget(key, initial_value, tooltip=tooltip)
    elif key_type == float:
        return FloatOptionWidget(key, initial_value, tooltip=tooltip)
    elif key_type == bool:
        return CheckboxOptionWidget(key, initial_value, tooltip=tooltip)
    else:
        raise ValueError('Unsupported option type: ' + str(type(initial_value)))
