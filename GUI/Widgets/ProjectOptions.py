import logging
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QDialog
from PySide6.QtCore import Signal, QSignalBlocker
from GUI.TranslatorOptions import TranslatorOptionsDialog

from GUI.Widgets.Widgets import OptionsGrid, TextBoxEditor
from PySubtitle.Options import Options
from PySubtitle.Helpers import ParseCharacters, ParseSubstitutions

class ProjectOptions(QGroupBox):
    """
    Allow the user to edit project-specific options
    """
    optionsChanged = Signal(dict)

    _gpt_options = {}

    def __init__(self, options=None):
        super().__init__()
        self.setTitle("Project Options")
        self.setMinimumWidth(450)
        self.layout = QVBoxLayout(self)
        self.grid_layout = OptionsGrid()

        options = options if options else {}

        # Add options
        self.AddSingleLineOption(0, "Movie Name", options, 'movie_name')
        self.AddSingleLineOption(1, "Target Language", options, 'target_language')
        self.AddCheckboxOption(2, "Include Original Text", options, 'include_original')
        self.AddMultiLineOption(3, "Description", options, 'description')
        self.AddMultiLineOption(4, "Characters", options, 'characters')
        self.AddMultiLineOption(5, "Substitutions", options, 'substitutions')
        self.AddCheckboxOption(6, "Match Partial Words", options, 'match_partial_words')
        self.AddButtonOption(7, "", "GPT Settings", self._gpt_settings)

        self.Populate(options)

        self.layout.addLayout(self.grid_layout)

    def GetOptions(self):
        """
        Get a dictionary of the user's options
        """
        options = {
            "movie_name": self.movie_name_input.text(),
            "target_language": self.target_language_input.text(),
            "include_original": self.include_original_input.isChecked(),
            "description": self.description_input.toPlainText(),
            "characters": ParseCharacters(self.characters_input.toPlainText()),
            "substitutions": ParseSubstitutions(self.substitutions_input.toPlainText()),
            "match_partial_words": self.match_partial_words_input.isChecked()
        }

        options.update(self._gpt_options)
        return options

    def AddSingleLineOption(self, row, label, options, key):
        # Add label and input field for a single-line option
        label_widget = QLabel(label)
        input_widget = QLineEdit()
        input_widget.setText(options.get(key, ""))
        input_widget.editingFinished.connect(self._text_changed)
        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)

    def AddMultiLineOption(self, row, label, options, key):
        # Add label and input field for a multi-line option
        label_widget = QLabel(label)
        input_widget = TextBoxEditor()
        input_widget.setAcceptRichText(False)
        value = options.get(key, "")
        if isinstance(value, list):
            value = '\n'.join(value)
        input_widget.setPlainText(value)

        input_widget.editingFinished.connect(self._text_changed)
        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)

    def AddCheckboxOption(self, row, label, options, key):
        label_widget = QLabel(label)
        input_widget = QCheckBox(self)
        value = options.get(key, False)
        input_widget.setChecked(value)
        input_widget.stateChanged.connect(self._check_changed)

        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)

    def AddButtonOption(self, row, label, text, callable):
        label_widget = QLabel(label)
        button_widget = QPushButton(text)
        button_widget.clicked.connect(callable)
        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(button_widget, row, 1)        

    def Populate(self, options):
        if isinstance(options, Options):
            return self.Populate(options.options)

        self.api_key = options.get('api_key')

        self._gpt_options = {
            'api_key': options.get('api_key'),
            'gpt_model': options.get('gpt_model'),
            'gpt_prompt': options.get('gpt_prompt'),
            'instructions': options.get('instructions'),
            'retry_instructions': options.get('retry_instructions'),
            'instruction_file': options.get('instruction_file'),
            'min_batch_size' : options.get('min_batch_size'),
            'max_batch_size' : options.get('max_batch_size'),
            'batch_threshold' : options.get('batch_threshold'),
            'scene_threshold' : options.get('scene_threshold'),
        }

        with QSignalBlocker(self):
            for key in options:
                if hasattr(self, key + "_input"):
                    value = options.get(key)
                    self._setvalue(key, value)

    def Clear(self):
        with QSignalBlocker(self):
            for key in ["movie_name", "description", "characters", "substitutions", "match_partial_words", "include_original"]:
                input = getattr(self, key + "_input")
                if input:
                    if isinstance(input, QCheckBox):
                        input.setChecked(False)
                    else:
                        input.clear()
                else:
                    logging.error(f"No input found for {key}")
        
    def _setvalue(self, key, value):
        if isinstance(value, bool):
            getattr(self, key + "_input").setChecked(value or False)
        else:
            self._settext(key, value)

    def _settext(self, key, value):
        if isinstance(value, list):
            value = '\n'.join(value)
        elif isinstance(value, dict):
            items = [ f"{k}::{v}" for k, v in value.items() ]
            value = '\n'.join(items)
        getattr(self, key + "_input").setText(value or "")

    def _text_changed(self, text = None):
        options = self.GetOptions()
        self.optionsChanged.emit(options)

    def _check_changed(self, int = None):
        options = self.GetOptions()
        self.optionsChanged.emit(options)

    def _gpt_settings(self):
        dialog = TranslatorOptionsDialog(self._gpt_options, parent=self)
        result = dialog.exec()

        if result == QDialog.Accepted:
            logging.info("GPT Options for this project updated")
            self.optionsChanged.emit(self._gpt_options)
