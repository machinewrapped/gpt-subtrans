from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleValidator import SubtitleValidator

import logging

class AutoSplitBatchCommand(Command):
    def __init__(self, scene_number : int, batch_number : int, datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_number = batch_number
        self.split_line = None

    def execute(self):
        logging.info(f"Auto-splitting batch {str(self.scene_number)} batch {str(self.batch_number)}")

        project : SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise CommandError("No subtitles", command=self)

        scene = project.subtitles.GetScene(self.scene_number)

        if not scene or not scene.GetBatch(self.batch_number):
            raise CommandError(f"Cannot find scene {self.scene_number} batch {self.batch_number}", command=self)

        min_batch_size = self.datamodel.project_options.get('min_batch_size', 1)
        scene.AutoSplitBatch(self.batch_number, min_batch_size)

        new_batch_number = self.batch_number + 1

        split_batch : SubtitleBatch = scene.GetBatch(self.batch_number)
        new_batch : SubtitleBatch = scene.GetBatch(new_batch_number)

        validator = SubtitleValidator(self.datamodel.project_options)
        validator.ValidateBatch(split_batch)
        validator.ValidateBatch(new_batch)

        # Remove lines from the original batch that are in the new batch now
        model_update = self.AddModelUpdate()
        for line_removed in range(new_batch.first_line_number, new_batch.last_line_number + 1):
            model_update.lines.remove((self.scene_number, self.batch_number, line_removed))

        for batch_number in range(self.batch_number + 1, len(scene.batches)):
             model_update.batches.update((self.scene_number, batch_number), { 'number' : batch_number + 1})

        model_update.batches.update((self.scene_number, self.batch_number), { 'errors' : split_batch.errors })
        model_update.batches.add((self.scene_number, new_batch_number), scene.GetBatch(new_batch_number))

        self.split_line = new_batch.first_line_number
        self.can_undo = True
        return True

    def undo(self):
        project: SubtitleProject = self.datamodel.project

        scene = project.subtitles.GetScene(self.scene_number)

        if not scene or not scene.GetBatch(self.batch_number):
            raise CommandError(f"Cannot find scene {self.scene_number} batch {self.batch_number}", command=self)

        scene.MergeBatches([self.batch_number, self.batch_number + 1])

        merged_batch = scene.GetBatch(self.batch_number)

        model_update = self.AddModelUpdate()
        model_update.batches.remove((self.scene_number, self.batch_number + 1))
        model_update.batches.update((self.scene_number, self.batch_number), { 'errors' : merged_batch.errors })

        model_update = self.AddModelUpdate()
        for line_number in range(self.split_line, merged_batch.last_line_number + 1):
            key = (self.scene_number, self.batch_number, line_number)
            line = merged_batch.GetOriginalLine(line_number)
            line.translated = merged_batch.GetTranslatedLine(line_number)
            model_update.lines.add(key, line)

        return True