from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QLineEdit
from PySide6.QtCore import Signal

from GUI.Widgets.Widgets import OptionsGrid, TextBoxEditor

class ProjectOptions(QGroupBox):
    """
    Allow the user to edit project-specific options
    """
    optionsChanged = Signal(dict)

    def __init__(self, options=None):
        super().__init__()
        self.setTitle("Project Options")
        self.setMinimumWidth(400)
        self.layout = QVBoxLayout(self)
        self.grid_layout = OptionsGrid()

        options = options if options else {}

        # Add options
        self.AddSingleLineOption(0, "Movie Name", options, 'movie_name')
        self.AddSingleLineOption(1, "GPT Model", options, 'gpt_model')
        self.AddSingleLineOption(2, "GPT Prompt", options, 'gpt_prompt')
        self.AddMultiLineOption(3, "Synopsis", options, 'synopsis')
        self.AddMultiLineOption(4, "Characters", options, 'characters')
        self.AddMultiLineOption(5, "Substitutions", options, 'substitutions')

        # Add grid layout to main layout
        self.layout.addLayout(self.grid_layout)

    def get_options(self):
        # Return a dictionary containing the user input
        return {
            "movie_name": self.movie_name_input.text(),
            "gpt_model": self.gpt_model_input.text(),
            "gpt_prompt": self.gpt_prompt_input.text(),
            "synopsis": self.synopsis_input.toPlainText(),
            "characters": self.characters_input.toPlainText(),
            "substitutions": self.substitutions_input.toPlainText(),
        }

    def AddSingleLineOption(self, row, label, options, key):
        # Add label and input field for a single-line option
        label_widget = QLabel(label)
        input_widget = QLineEdit()
        input_widget.setText(options.get(key, ""))
        input_widget.editingFinished.connect(self.text_changed)
        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)

    def AddMultiLineOption(self, row, label, options, key):
        # Add label and input field for a multi-line option
        label_widget = QLabel(label)
        input_widget = TextBoxEditor()
        input_widget.setText(options.get(key, ""))
        input_widget.editingFinished.connect(self.text_changed)
        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)

    def populate(self, options):
        for key in options:
            if hasattr(self, key + "_input"):
                getattr(self, key + "_input").setText(options.get(key) or "")

    def clear(self):
        for key in ["movie_name", "gpt_model", "gpt_prompt", "synopsis", "characters", "substitutions"]:
            getattr(self, key + "_input").setText("")

    def text_changed(self, text = None):
        options = self.get_options()
        self.optionsChanged.emit(options)