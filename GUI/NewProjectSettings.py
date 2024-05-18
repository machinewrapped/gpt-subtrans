from copy import deepcopy
import logging
import os

from PySide6.QtCore import Qt, QThread, Signal, Slot, QRecursiveMutex, QMutexLocker
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QDialogButtonBox, QFormLayout, QFrame, QLabel)

from GUI.ProjectDataModel import ProjectDataModel
from GUI.Widgets.OptionsWidgets import CreateOptionWidget, DropdownOptionWidget

from PySubtitle.Instructions import GetInstructionFiles, LoadInstructionsResource
from PySubtitle.SubtitleBatcher import CreateSubtitleBatcher, BaseSubtitleBatcher
from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.SubtitleProcessor import SubtitleProcessor
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleScene import SubtitleScene

if os.environ.get("DEBUG_MODE") == "1":
    try:
        import debugpy # type: ignore
    except ImportError:
        pass

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
            try:
                field = CreateOptionWidget(key, self.settings[key], key_type, tooltip=tooltip)
                field.contentChanged.connect(lambda setting=field: self._on_setting_changed(setting.key, setting.GetValue()), type=Qt.ConnectionType.QueuedConnection)
                self.form_layout.addRow(field.name, field)
                self.fields[key] = field

            except Exception as e:
                logging.error(f"Unable to create option widget for {key}: {e}")

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(settings_widget)

        self.preview_widget = QLabel(self)
        self.layout.addWidget(self.preview_widget)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.buttonBox.accepted.connect(self.accept, type=Qt.ConnectionType.QueuedConnection)
        self.layout.addWidget(self.buttonBox)

        self.fields['instruction_file'].contentChanged.connect(self._update_instruction_file, type=Qt.ConnectionType.QueuedConnection)

        self.preview_threads = []
        self.preview_count = 0
        self.preview_mutex = QRecursiveMutex()

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
                    if instructions.target_language:
                        self.settings['target_language'] = instructions.target_language

                    logging.debug(f"Prompt: {instructions.prompt}")
                    logging.debug(f"Instructions: {instructions.instructions}")

                except Exception as e:
                    logging.error(f"Unable to load instructions from {instructions_file}: {e}")

        except Exception as e:
            logging.error(f"Unable to update settings: {e}")

        # Wait for any remaining preview threads to complete
        self._wait_for_threads()

        super(NewProjectSettings, self).accept()

    def _on_setting_changed(self, key, value):
        if key == 'provider':
            self._update_provider_settings(value)
        else:
            self.settings[key] = value
            if value is not None:
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
                if instructions.target_language:
                    self.fields['target_language'].SetValue(instructions.target_language)
            except Exception as e:
                logging.error(f"Unable to load instructions from {instruction_file}: {e}")

    def _preview_batches(self):
        try:
            self._update_settings()
            self._update_inputs()

            self.preview_count += 1
            preview_thread = BatchPreviewWorker(self.preview_count, self.settings, self.project.subtitles.originals)
            preview_thread.update_preview.connect(self._update_preview_widget, type=Qt.ConnectionType.QueuedConnection)
            preview_thread.finished.connect(self._remove_preview_thread, type=Qt.ConnectionType.QueuedConnection)
            preview_thread.start()

            with QMutexLocker(self.preview_mutex):
                self.preview_threads.append(preview_thread)

        except Exception as e:
            logging.error(f"Unable to preview batches: {e}")

    @Slot(int, str)
    def _update_preview_widget(self, count : int, text : str):
        if count == self.preview_count:
            with QMutexLocker(self.preview_mutex):
                self.preview_widget.setText(text)
                self.preview_threads = [x for x in self.preview_threads if x.count != count]

    @Slot()
    def _remove_preview_thread(self):
        with QMutexLocker(self.preview_mutex):
            self.preview_threads = [x for x in self.preview_threads if x != self.sender()]

    def _wait_for_threads(self):
        if self.preview_threads:
            QThread.msleep(500)
            with QMutexLocker(self.preview_mutex):
                for thread in self.preview_threads:
                    thread.update_preview.disconnect(self._update_preview_widget)
                    thread.finished.disconnect(self._remove_preview_thread)
                    thread.quit()
                    thread.wait()

class BatchPreviewWorker(QThread):
    update_preview = Signal(int, str)

    def __init__(self, count : int, settings : dict, subtitles : list[SubtitleLine], parent=None):
        super().__init__(parent)
        self.count = count
        self.settings = deepcopy(settings)
        self.subtitles = deepcopy(subtitles)

    def run(self):
        if 'debugpy' in globals():
            debugpy.debug_this_thread()

        try:
            if self.settings.get('preprocess_subtitles'):
                preprocessor = SubtitleProcessor(self.settings)
                lines = preprocessor.PreprocessSubtitles(self.subtitles)
            else:
                lines = self.subtitles

            batcher : BaseSubtitleBatcher = CreateSubtitleBatcher(self.settings)
            if batcher.max_batch_size < batcher.min_batch_size:
                self.update_preview.emit(self.count, "Max batch size is less than min batch size")
                return

            scenes : list[SubtitleScene] = batcher.BatchSubtitles(lines)
            batch_count = sum(scene.size for scene in scenes)
            line_count = sum(scene.linecount for scene in scenes)

            preview_text = f"{line_count} lines in {len(scenes)} scenes and {batch_count} batches"
            self.update_preview.emit(self.count, preview_text)

        except Exception as e:
            self.update_preview.emit(self.count, f"Error: {e}")