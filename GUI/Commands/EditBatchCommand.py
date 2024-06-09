from copy import deepcopy
from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleFile import SubtitleFile

import logging

class EditBatchCommand(Command):
    def __init__(self, scene_number : int, batch_number : int, edit : dict, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_number = batch_number
        self.edit = deepcopy(edit)
        self.undo_data = None

    def execute(self):
        logging.debug(f"Editing batch ({self.scene_number},{self.batch_number})")

        subtitles : SubtitleFile = self.datamodel.project.subtitles
        if not subtitles:
            raise CommandError("Unable to edit batch because datamodel is invalid", command=self)

        if not isinstance(self.edit, dict):
            raise CommandError("Edit data must be a dictionary", command=self)

        with subtitles.lock:
            batch : SubtitleBatch = subtitles.GetBatch(self.scene_number, self.batch_number)
            if not batch:
                raise CommandError(f"Batch ({self.scene_number},{self.batch_number}) not found", command=self)

            self.undo_data = {
                "summary": batch.summary,
            }

            batch.summary = self.edit.get('summary', batch.summary)

            self._update_viewmodel(batch)

        return True

    def undo(self):
        logging.debug(f"Undoing edit batch ({self.scene_number},{self.batch_number})")

        subtitles : SubtitleFile = self.datamodel.project.subtitles

        with subtitles.lock:
            batch : SubtitleBatch = subtitles.GetBatch(self.scene_number, self.batch_number)
            if not batch:
                raise CommandError(f"Batch ({self.scene_number},{self.batch_number}) not found", command=self)

            batch.summary = self.undo_data.get('summary', batch.summary)

            self._update_viewmodel(batch)

        return True

    def _update_viewmodel(self, batch : SubtitleBatch):
        viewmodel_update = self.AddModelUpdate()
        viewmodel_update.batches.update((self.scene_number, self.batch_number), { 'summary': batch.summary })

