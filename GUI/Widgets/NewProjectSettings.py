from PySide6.QtWidgets import (QDialog, QVBoxLayout, QDialogButtonBox, QFormLayout, QFrame, QLabel)

from GUI.Widgets.OptionsWidgets import CreateOptionWidget
from PySubtitleGPT import SubtitleProject
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleBatcher import SubtitleBatcher
from PySubtitleGPT.SubtitleScene import SubtitleScene

class NewProjectSettings(QDialog):
    SETTINGS = {
        'target_language': (str, "Language to translate the subtitles to"),
        'min_batch_size': (int, "Fewest lines to send in separate batch"),
        'max_batch_size': (int, "Most lines to send in each batch"),
        'scene_threshold': (float, "Number of seconds gap to consider it a new scene"),
        'batch_threshold': (float, "Number of seconds gap to consider starting a new batch"),
        'gpt_prompt': (str, "High-level instructions for the translator"),
        'instruction_file': (str, "Detailed instructions for the translator")
    }

    def __init__(self, project : SubtitleProject, parent=None):
        super(NewProjectSettings, self).__init__(parent)
        self.setWindowTitle("Project Settings")
        self.setMinimumWidth(800)

        self.project : SubtitleProject = project
        self.settings : dict = project.options.GetSettings()

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

    def accept(self):
        self._update_settings()

        self.project.options.update(self.settings)

        super(NewProjectSettings, self).accept()

    def reject(self):
        super(NewProjectSettings, self).reject()

