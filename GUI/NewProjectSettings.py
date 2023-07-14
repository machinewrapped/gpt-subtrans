from PySide6.QtWidgets import (QDialog, QVBoxLayout, QDialogButtonBox, QFormLayout, QFrame, QLabel)
from GUI.GuiHelpers import GetInstructionFiles

from GUI.Widgets.OptionsWidgets import CreateOptionWidget
from PySubtitleGPT import SubtitleProject
from PySubtitleGPT.Options import LoadInstructionsFile, Options
from PySubtitleGPT.SubtitleBatcher import SubtitleBatcher
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleTranslator import SubtitleTranslator

class NewProjectSettings(QDialog):
    SETTINGS = {
        'target_language': (str, "Language to translate the subtitles to"),
        'min_batch_size': (int, "Fewest lines to send in separate batch"),
        'max_batch_size': (int, "Most lines to send in each batch"),
        'scene_threshold': (float, "Number of seconds gap to consider it a new scene"),
        'batch_threshold': (float, "Number of seconds gap to consider starting a new batch"),
        'gpt_model': (str, "AI model to use as the translator"),
        'gpt_prompt': (str, "High-level instructions for the translator"),
        'instruction_file': (str, "Detailed instructions for the translator")
    }

    def __init__(self, project : SubtitleProject, parent=None):
        super(NewProjectSettings, self).__init__(parent)
        self.setWindowTitle("Project Settings")
        self.setMinimumWidth(800)

        self.project : SubtitleProject = project
        self.settings : dict = project.options.GetSettings()
        api_key = project.options.api_key()
        api_base = project.options.api_base()

        if api_key:
            models = SubtitleTranslator.GetAvailableModels(api_key, api_base)
            self.SETTINGS['gpt_model'] = (models, self.SETTINGS['gpt_model'][1])

        instruction_files = GetInstructionFiles()
        if instruction_files:
            self.SETTINGS['instruction_file'] = (instruction_files, self.SETTINGS['instruction_file'][1])

        settings_widget = QFrame(self)

        self.form_layout = QFormLayout(settings_widget)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        for key, setting in self.SETTINGS.items():
            key_type, tooltip = setting
            field = CreateOptionWidget(key, self.settings[key], key_type, tooltip=tooltip)
            field.contentChanged.connect(self._preview_batches)
            self.form_layout.addRow(field.name, field)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(settings_widget)

        self.preview_widget = QLabel(self)
        self.layout.addWidget(self.preview_widget)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.buttonBox.accepted.connect(self.accept)
        self.layout.addWidget(self.buttonBox)

        self._preview_batches()

    def accept(self):
        self._update_settings()

        instructions_file = self.settings.get('instruction_file')
        if instructions_file:
            instructions, retry_instructions = LoadInstructionsFile(instructions_file)
            if instructions:
                self.settings['instructions'] = instructions
            if retry_instructions:
                self.settings['retry_instructions'] = retry_instructions

        self.project.options.update(self.settings)

        super(NewProjectSettings, self).accept()

    def _update_settings(self):
        layout = self.form_layout.layout()

        for row in range(layout.rowCount()):
            field = layout.itemAt(row, QFormLayout.FieldRole).widget()
            self.settings[field.key] = field.GetValue()

    def _preview_batches(self):
        self._update_settings()
        batcher = SubtitleBatcher(self.settings)
        scenes : list[SubtitleScene] = batcher.BatchSubtitles(self.project.subtitles.originals)
        batch_count = sum(scene.size for scene in scenes)
        line_count = sum(scene.linecount for scene in scenes)
        self.preview_widget.setText(f"{line_count} lines in {len(scenes)} scenes and {batch_count} batches")
