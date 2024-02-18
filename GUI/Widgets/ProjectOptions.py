import logging
from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QComboBox,
    QDialog,
    QFileDialog
)
from PySide6.QtCore import Signal, QSignalBlocker
from GUI.EditInstructionsDialog import EditInstructionsDialog

from GUI.Widgets.Widgets import OptionsGrid, TextBoxEditor
from PySubtitle.Options import Options
from PySubtitle.Helpers import ParseNames, ParseSubstitutions
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator

class ProjectOptions(QGroupBox):
    """
    Allow the user to edit project-specific options
    """
    settingsChanged = Signal(dict)

    def __init__(self, settings=None):
        super().__init__()
        self.setTitle("Project Settings")
        self.setMinimumWidth(450)
        self.layout = QVBoxLayout(self)
        self.grid_layout = OptionsGrid()

        self.settings = settings or {}
        self.model_list = []

        # Add options
        self.AddSingleLineOption(0, "Movie Name", self.settings, 'movie_name')
        self.AddSingleLineOption(1, "Target Language", self.settings, 'target_language')
        self.AddCheckboxOption(2, "Include Original Text", self.settings, 'include_original')
        self.AddMultiLineOption(3, "Description", self.settings, 'description')
        self.AddMultiLineOption(4, "Names", self.settings, 'names')
        self.AddMultiLineOption(5, "Substitutions", self.settings, 'substitutions')
        self.AddCheckboxOption(6, "Substitute Partial Words", self.settings, 'match_partial_words')
        self.AddDropdownOption(7, "Model", self.settings, 'model', self.model_list)
        self.AddButtonOption(8, "", "Edit Instructions", self._edit_instructions)
        self.AddButtonOption(9, "", "Copy From Another Project", self._copy_from_another_project)

        self.Populate(self.settings)

        self.layout.addLayout(self.grid_layout)

    def GetSettings(self):
        """
        Get a dictionary of the user's settings
        """
        settings = {
            "movie_name": self.movie_name_input.text(),
            "target_language": self.target_language_input.text(),
            "include_original": self.include_original_input.isChecked(),
            "description": self.description_input.toPlainText(),
            "names": ParseNames(self.names_input.toPlainText()),
            "substitutions": ParseSubstitutions(self.substitutions_input.toPlainText()),
            "match_partial_words": self.match_partial_words_input.isChecked(),
            "model": self.model_input.currentText(),
        }

        return settings

    def AddSingleLineOption(self, row, label, settings, key):
        # Add label and input field for a single-line option
        label_widget = QLabel(label)
        input_widget = QLineEdit()
        input_widget.setText(settings.get(key, ""))
        input_widget.editingFinished.connect(self._text_changed)
        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)

    def AddMultiLineOption(self, row, label, settings, key):
        # Add label and input field for a multi-line option
        label_widget = QLabel(label)
        input_widget = TextBoxEditor()
        input_widget.setAcceptRichText(False)
        value = settings.get(key, "")
        if isinstance(value, list):
            value = '\n'.join(value)
        input_widget.setPlainText(value)

        input_widget.editingFinished.connect(self._text_changed)
        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)

    def AddCheckboxOption(self, row, label, settings, key):
        label_widget = QLabel(label)
        input_widget = QCheckBox(self)
        value = settings.get(key, False)
        input_widget.setChecked(value)
        input_widget.stateChanged.connect(self._check_changed)

        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(input_widget, row, 1)
        setattr(self, key + "_input", input_widget)

    def AddDropdownOption(self, row, label, settings, key, values):
        label_widget = QLabel(label)
        combo_box = QComboBox(self)
        combo_box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        for value in values:
            combo_box.addItem(value)

        if key in settings:
            initial_value = settings[key]
            combo_box.setCurrentIndex(combo_box.findText(initial_value))

        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(combo_box, row, 1)
        setattr(self, key + "_input", combo_box)

    def AddButtonOption(self, row, label, text, callable):
        label_widget = QLabel(label)
        button_widget = QPushButton(text)
        button_widget.clicked.connect(callable)
        self.grid_layout.addWidget(label_widget, row, 0)
        self.grid_layout.addWidget(button_widget, row, 1)

    def OpenOptions(self):
        self.settings['model'] = self.settings.get('model')

        self.model_list = SubtitleTranslator.GetAvailableModels(self.settings)
    
        model_input = getattr(self, "model_input")
        if model_input:
            model_input.clear()
            model_input.addItems(self.model_list)
            self._update_combo_box(model_input, self.settings['model'])

        self.show()

    def Populate(self, settings):
        if isinstance(settings, Options):
            return self.Populate(settings.options)

        if not self.model_list:
            self.model_list = [ settings.get('model') ]

        with QSignalBlocker(self):
            for key in settings:
                if hasattr(self, key + "_input"):
                    value = settings.get(key)
                    self._setvalue(key, value)

        self.settings = settings

    def Clear(self):
        with QSignalBlocker(self):
            for key in ["movie_name", "description", "names", "substitutions", "match_partial_words", "include_original", "model"]:
                input = getattr(self, key + "_input")
                if input:
                    if isinstance(input, QCheckBox):
                        input.setChecked(False)
                    else:
                        input.clear()
                else:
                    logging.error(f"No input found for {key}")
        
    def _setvalue(self, key, value):
        widget = getattr(self, key + "_input")
        if isinstance(widget, QCheckBox):
            widget.setChecked(value or False)
        elif isinstance(widget, QComboBox):
            self._update_combo_box(widget, value)
        else:
            self._settext(widget, value)

    def _settext(self, widget, value):
        if isinstance(value, list):
            value = '\n'.join(value)
        elif isinstance(value, dict):
            items = [ f"{k}::{v}" for k, v in value.items() ]
            value = '\n'.join(items)
        widget.setText(value or "")

    def _update_combo_box(self, widget, value):
        index = widget.findText(value)
        if index >= 0:
            widget.setCurrentIndex(index)

    def _text_changed(self, text = None):
        settings = self.GetSettings()
        self.settingsChanged.emit(settings)

    def _check_changed(self, int = None):
        settings = self.GetSettings()
        self.settingsChanged.emit(settings)

    def _edit_instructions(self):
        dialog = EditInstructionsDialog(self.settings, parent=self)
        result = dialog.exec()

        if result == QDialog.Accepted:
            logging.info("Instructions for this project updated")
            self.settings.update(dialog.instructions.GetSettings())
            self.settingsChanged.emit(dialog.instructions.GetSettings())

    def _copy_from_another_project(self):
        '''
        Copy project settings from another project file
        '''
        dialog_options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select project to copy settings from", "", "Subtrans Files (*.subtrans);;All Files (*)", options=dialog_options)
        if file_name:
            try:
                project_options = Options({"project": 'read'})
                source : SubtitleProject = SubtitleProject(project_options)
                subtitles : SubtitleFile = source.ReadProjectFile(file_name)
                if not subtitles:
                    raise Exception("Invalid project file")

                self.Populate(subtitles.settings)

            except Exception as e:
                logging.error(f"Unable to read project file: {str(e)}")
