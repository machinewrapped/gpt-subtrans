from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QTextEdit, QPushButton

class OptionsGrid(QGridLayout):
    def __init__(self, parent = None) -> None:
        super().__init__(parent)

class ProjectOptionsDialog(QDialog):
    def __init__(self, options=None):
        super().__init__()

        self.setWindowTitle("Project Options")
        self.layout = QVBoxLayout(self)
        grid_layout = OptionsGrid(self)

        # Add options
        self.AddSingleLineOption(grid_layout, 0, "Movie Name", options, 'movie_name')
        self.AddSingleLineOption(grid_layout, 1, "GPT Model", options, 'gpt_model')
        self.AddSingleLineOption(grid_layout, 2, "GPT Prompt", options, 'gpt_prompt')
        self.AddMultiLineOption(grid_layout, 3, "Synopsis", options, 'synopsis')
        self.AddMultiLineOption(grid_layout, 4, "Characters", options, 'characters')
        self.AddMultiLineOption(grid_layout, 5, "Substitutions", options, 'substitutions')

        # Add grid layout to main layout
        self.layout.addLayout(grid_layout)

        # Add OK and Cancel buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        self.layout.addLayout(buttons_layout)

        self.setLayout(self.layout)

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

    def AddSingleLineOption(self, layout, row, label, options, key):
        # Add label and input field for a single-line option
        label_widget = QLabel(label)
        input_widget = QLineEdit()
        input_widget.setText(options.get(key, ""))
        layout.addWidget(label_widget, row, 0)
        layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)

    def AddMultiLineOption(self, layout, row, label, options, key):
        # Add label and input field for a multi-line option
        label_widget = QLabel(label)
        input_widget = QTextEdit()
        input_widget.setText(options.get(key, ""))
        layout.addWidget(label_widget, row, 0)
        layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)
