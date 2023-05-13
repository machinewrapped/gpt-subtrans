import logging
from PySide6.QtWidgets import (QWidget, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit, QSizePolicy, QHBoxLayout)

class OptionWidget(QWidget):
    def __init__(self, key, initial_value, parent=None):
        super(OptionWidget, self).__init__(parent)
        self.key = key
        self.name = self.generate_name(key)
        self.initial_value = initial_value
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    @staticmethod
    def generate_name(key):
        return key.replace('_', ' ').title()

    def get_value(self):
        raise NotImplementedError

class TextOptionWidget(OptionWidget):
    def __init__(self, key, initial_value):
        super(TextOptionWidget, self).__init__(key, initial_value)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.text_field = QLineEdit(self)
        self.text_field.setText(initial_value)
        self.text_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout.addWidget(self.text_field)

    def get_value(self):
        return self.text_field.text()

class IntegerOptionWidget(OptionWidget):
    def __init__(self, key, initial_value):
        super(IntegerOptionWidget, self).__init__(key, initial_value)
        self.spin_box = QSpinBox(self)
        self.spin_box.setValue(initial_value)

    def get_value(self):
        return self.spin_box.value()

class FloatOptionWidget(OptionWidget):
    def __init__(self, key, initial_value):
        super(FloatOptionWidget, self).__init__(key, initial_value)
        self.double_spin_box = QDoubleSpinBox(self)
        self.double_spin_box.setValue(initial_value)

    def get_value(self):
        return self.double_spin_box.value()

class CheckboxOptionWidget(OptionWidget):
    def __init__(self, key, initial_value):
        super(CheckboxOptionWidget, self).__init__(key, initial_value)
        self.check_box = QCheckBox(self)
        self.check_box.setChecked(initial_value)

    def get_value(self):
        return self.check_box.isChecked()

class DropdownOptionWidget(OptionWidget):
    def __init__(self, key, values, initial_value):
        super(DropdownOptionWidget, self).__init__(key, initial_value)
        self.combo_box = QComboBox(self)
        for value in values:
            self.combo_box.addItem(value)
        self.combo_box.setCurrentIndex(self.combo_box.findText(initial_value))

    def get_value(self):
        return self.combo_box.currentText()

def CreateOptionWidget(key, initial_value):
    # Helper function to create an OptionWidget based on the type of the initial value
    if isinstance(initial_value, str):
        return TextOptionWidget(key, initial_value)
    elif isinstance(initial_value, int):
        return IntegerOptionWidget(key, initial_value)
    elif isinstance(initial_value, float):
        return FloatOptionWidget(key, initial_value)
    elif isinstance(initial_value, bool):
        return CheckboxOptionWidget(key, initial_value)
    elif initial_value is None:
        logging.debug(f"Initial value for {key} is None, assuming text")
        return TextOptionWidget(key, "")
    else:
        raise ValueError('Unsupported option type: ' + str(type(initial_value)))

def CreateDropdownOptionWidget(key, values, initial_value):
    return DropdownOptionWidget(key, values, initial_value)
