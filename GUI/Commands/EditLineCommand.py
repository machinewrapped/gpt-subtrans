import logging
from copy import deepcopy
from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ViewModel.ViewModelUpdate import ModelUpdate
from PySubtitle.Helpers.Time import GetTimeDelta
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.SubtitleFile import SubtitleFile

from PySubtitle.SubtitleValidator import SubtitleValidator

class EditLineCommand(Command):
    def __init__(self, line_number : int, edit : dict, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.line_number = line_number
        self.edit = deepcopy(edit)
        self.undo_data = None

    def execute(self):
        logging.debug(f"Editing line {self.line_number}")

        subtitles : SubtitleFile = self.datamodel.project.subtitles
        if not subtitles:
            raise CommandError("Unable to edit batch because datamodel is invalid", command=self)

        if not isinstance(self.edit, dict):
            raise CommandError("Edit data must be a dictionary", command=self)

        with subtitles.lock:
            batch : SubtitleBatch = subtitles.GetBatchContainingLine(self.line_number)
            if not batch:
                raise CommandError(f"Line {self.line_number} not found in any batch", command=self)

            line : SubtitleLine = batch.GetOriginalLine(self.line_number)
            if not line:
                raise CommandError(f"Line {self.line_number} not found in batch ({batch.scene},{batch.number})", command=self)

            self.undo_data = {
            }

            if 'start' in self.edit:
                self.undo_data['start'] = line.start
                line.start = GetTimeDelta(self.edit['start'])

            if 'end' in self.edit:
                self.undo_data['end'] = line.end
                line.end = GetTimeDelta(self.edit['end'])

            if 'text' in self.edit:
                self.undo_data['text'] = line.text
                line.text = self.edit['text']

            if 'translation' in self.edit:
                translated_line : SubtitleLine = batch.GetTranslatedLine(self.line_number)

                if translated_line:
                    self.undo_data['translation'] = translated_line.text
                    translated_line.text = self.edit['translation']
                    translated_line.original = line.text
                    line.translation = translated_line.text
                else:
                    self.undo_data['translation'] = line.translation
                    line.translation = self.edit['translation']
                    translated_line = line.translated
                    translated_line.original = line.text
                    batch.AddTranslatedLine(translated_line)

            self._update_model(batch, line)

        return True

    def undo(self):
        logging.debug(f"Undoing edit line {self.line_number}")

        subtitles : SubtitleFile = self.datamodel.project.subtitles

        with subtitles.lock:
            batch : SubtitleBatch = subtitles.GetBatchContainingLine(self.line_number)
            if not batch:
                raise CommandError(f"Line {self.line_number} not found in any batch", command=self)

            line : SubtitleLine = batch.GetOriginalLine(self.line_number)
            if not line:
                raise CommandError(f"Line {self.line_number} not found in batch ({batch.scene},{batch.number})", command=self)

            if 'start' in self.undo_data:
                line.start = self.undo_data['start']

            if 'end' in self.undo_data:
                line.end = self.undo_data['end']

            if 'text' in self.undo_data:
                line.text = self.undo_data['text']

            if 'translation' in self.undo_data:
                line.translation = self.undo_data['translation']
                translated_line = batch.GetTranslatedLine(self.line_number)
                if translated_line:
                    translated_line.start = line.start
                    translated_line.end = line.end
                    translated_line.text = self.undo_data['translation']
                    translated_line.original = line.text

            self._update_model(batch, line)

        return True

    def _update_model(self, batch : SubtitleBatch, line : SubtitleLine):
        viewmodel_update : ModelUpdate = self.AddModelUpdate()
        viewmodel_update.lines.update((batch.scene, batch.number, self.line_number), {
                                            'start': line.start,
                                            'end': line.end,
                                            'text': line.text,
                                            'translation': line.translation
                                            })

        validator = SubtitleValidator(self.datamodel.project_options)
        self.errors = validator.ValidateBatch(batch)

        viewmodel_update.batches.update((batch.scene,batch.number), { 'errors': self.errors })

