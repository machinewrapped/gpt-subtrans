import re
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Signal

from GUI.Widgets.Widgets import OptionsGrid, TextBoxEditor
from PySubtitleGPT.Options import Options
from PySubtitleGPT.Helpers import ParseCharacters, ParseSubstitutions

class ProjectOptions(QGroupBox):
    """
    Allow the user to edit project-specific options
    """
    optionsChanged = Signal(dict)

    def __init__(self, options=None):
        super().__init__()
        self.setTitle("Project Options")
        self.setMinimumWidth(450)
        self.layout = QVBoxLayout(self)
        self.grid_layout = OptionsGrid()

        options = options if options else {}

        # Add options
        self.AddSingleLineOption(0, "Movie Name", options, 'movie_name')
        self.AddMultiLineOption(1, "Synopsis", options, 'synopsis')
        self.AddMultiLineOption(2, "Characters", options, 'characters')
        self.AddMultiLineOption(3, "Substitutions", options, 'substitutions')
        self.AddSingleLineOption(4, "GPT Model", options, 'gpt_model')
        self.AddSingleLineOption(5, "GPT Prompt", options, 'gpt_prompt')
        #TODO Add an "Edit Instructions" button

        self.layout.addLayout(self.grid_layout)

    def GetOptions(self):
        """
        Get a dictionary of the user's options
        """
        return {
            "movie_name": self.movie_name_input.text(),
            "gpt_model": self.gpt_model_input.text(),
            "gpt_prompt": self.gpt_prompt_input.text(),
            "synopsis": self.synopsis_input.toPlainText(),
            "characters": ParseCharacters(self.characters_input.toPlainText()),
            "substitutions": ParseSubstitutions(self.substitutions_input.toPlainText())
        }

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

    def Populate(self, options):
        if isinstance(options, Options):
            return self.Populate(options.options)

        for key in options:
            if hasattr(self, key + "_input"):
                self._settext(key, options.get(key))

    def Clear(self):
        for key in ["movie_name", "gpt_model", "gpt_prompt", "synopsis", "characters", "substitutions"]:
            getattr(self, key + "_input").setText("")

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