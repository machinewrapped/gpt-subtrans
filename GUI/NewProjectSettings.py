import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QDialogButtonBox, QFormLayout, QFrame, QLabel)

from GUI.ProjectDataModel import ProjectDataModel
from GUI.Widgets.OptionsWidgets import CreateOptionWidget, DropdownOptionWidget

from PySubtitle.Instructions import GetInstructionFiles, LoadInstructionsResource
from PySubtitle.SubtitleBatcher import CreateSubtitleBatcher
from PySubtitle.SubtitleProcessor import SubtitleProcessor
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleScene import SubtitleScene

class NewProjectSettings(QDialog):
    OPTIONS = {
        'target_language': (str, "Language to translate the subtitles to"),
        'provider': ([], "The AI translation service to use"),
        'model': (str, "AI model to use as the translator"),
        'scene_threshold': (float, "Number of seconds gap to consider it a new scene"),
        'min_batch_size': (int, "Fewest lines to send in separate batch"),
        'max_batch_size': (int, "Most lines to send in each batch"),
        'preprocess_subtitles': (bool, "Preprocess subtitles before batching"),
        'use_simple_batcher': (bool, "Use old batcher instead of batching dynamically based on gap size"),
        'batch_threshold': (float, "Number of seconds gap to consider starting a new batch (simple batcher)"),
        'instruction_file': (str, "Detailed instructions for the translator"),
        'prompt': (str, "High-level instructions for the translator")
    }

    def __init__(self, datamodel : ProjectDataModel, parent=None):
        super(NewProjectSettings, self).__init__(parent)
        self.setWindowTitle("Project Settings")
        self.setMinimumWidth(800)

        self.fields = {}

        self.datamodel = datamodel
        self.project : SubtitleProject = datamodel.project
        self.settings = datamodel.project_options.GetSettings()

        self.providers = datamodel.available_providers
        self.OPTIONS['provider'] = (self.providers, self.OPTIONS['provider'][1])
        self.settings['provider'] = datamodel.provider

        available_models = datamodel.available_models
        self.OPTIONS['model'] = (available_models, self.OPTIONS['model'][1])
        self.settings['model'] = datamodel.selected_model

        instruction_files = GetInstructionFiles()
        if instruction_files:
            self.OPTIONS['instruction_file'] = (instruction_files, self.OPTIONS['instruction_file'][1])

        settings_widget = QFrame(self)

        self.form_layout = QFormLayout(settings_widget)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        for key, setting in self.OPTIONS.items():
            key_type, tooltip = setting
            field = CreateOptionWidget(key, self.settings[key], key_type, tooltip=tooltip)
            field.contentChanged.connect(lambda setting=field: self._on_setting_changed(setting.key, setting.GetValue()))
            self.form_layout.addRow(field.name, field)
            self.fields[key] = field

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(settings_widget)

        self.preview_widget = QLabel(self)
        self.layout.addWidget(self.preview_widget)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.buttonBox.accepted.connect(self.accept)
        self.layout.addWidget(self.buttonBox)

        self.fields['instruction_file'].contentChanged.connect(self._update_instruction_file)

        self.preprocessor_settings = {
            'min_line_duration': self.settings.get('min_line_duration', 0.0),
            'max_line_duration': self.settings.get('max_line_duration', 0.0),
            'min_gap': self.settings.get('min_gap', 0.05),
            'min_split_chars': self.settings.get('min_split_chars', 4),
        }

        self._preview_batches()

    def accept(self):
        try:
            self._update_settings()

            instructions_file = self.settings.get('instruction_file')
            if instructions_file:
                logging.info(f"Project instructions set from {instructions_file}")
                try:
                    instructions = LoadInstructionsResource(instructions_file)

                    self.settings['prompt'] = instructions.prompt
                    self.settings['instructions'] = instructions.instructions
                    self.settings['retry_instructions'] = instructions.retry_instructions

                    logging.debug(f"Prompt: {instructions.prompt}")
                    logging.debug(f"Instructions: {instructions.instructions}")

                except Exception as e:
                    logging.error(f"Unable to load instructions from {instructions_file}: {e}")

        except Exception as e:
            logging.error(f"Unable to update settings: {e}")

        super(NewProjectSettings, self).accept()

    def _on_setting_changed(self, key, value):
        if key == 'provider':
            self._update_provider_settings(value)
        else:
            self.settings[key] = value
            self._preview_batches()

    def _update_provider_settings(self, provider : str):
        try:
            self.datamodel.UpdateProjectSettings({ "provider": provider})
            model_options : DropdownOptionWidget = self.fields['model']
            model_options.SetOptions(self.datamodel.available_models, self.datamodel.selected_model)
            self.settings['provider'] = provider
            self.settings['model'] = self.datamodel.selected_model
        except Exception as e:
            logging.error(f"Provider error: {e}")

    def _update_settings(self):
        layout = self.form_layout.layout()

        for row in range(layout.rowCount()):
            field = layout.itemAt(row, QFormLayout.FieldRole).widget()
            self.settings[field.key] = field.GetValue()

    def _preview_batches(self):
        self._update_settings()
        self._update_inputs()

        lines = self.project.subtitles.originals
        if self.settings.get('preprocess_subtitles'):
            preprocessor = SubtitleProcessor(self.preprocessor_settings)
            lines = preprocessor.PreprocessSubtitles(lines)

        batcher = CreateSubtitleBatcher(self.settings)
        if batcher.min_batch_size < batcher.max_batch_size:
            scenes : list[SubtitleScene] = batcher.BatchSubtitles(lines)
            batch_count = sum(scene.size for scene in scenes)
            line_count = sum(scene.linecount for scene in scenes)
            self.preview_widget.setText(f"{line_count} lines in {len(scenes)} scenes and {batch_count} batches")

    def _update_inputs(self):
        layout : QFormLayout = self.form_layout.layout()

        for row in range(layout.rowCount()):
            field = layout.itemAt(row, QFormLayout.ItemRole.FieldRole).widget()
            if field.key == 'batch_threshold':
                use_simple_batcher = self.settings.get('use_simple_batcher')
                field.setEnabled(use_simple_batcher)

    def _update_instruction_file(self):
        """ Update the prompt when the instruction file is changed """
        instruction_file = self.fields['instruction_file'].GetValue()
        if instruction_file:
            try:
                instructions = LoadInstructionsResource(instruction_file)
                self.fields['prompt'].SetValue(instructions.prompt)
            except Exception as e:
                logging.error(f"Unable to load instructions from {instruction_file}: {e}")
