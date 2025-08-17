from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleValidator import SubtitleValidator
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.Helpers.Localization import _

import logging

class DeleteLinesCommand(Command):
    """
    Delete one or several lines
    """
    def __init__(self, line_numbers : list[int], datamodel: ProjectDataModel|None = None):
        super().__init__(datamodel)
        self.line_numbers = line_numbers
        self.deletions = []

    def execute(self):
        if not self.line_numbers:
            raise CommandError(_("No lines selected to delete"), command=self)

        logging.info(_("Deleting lines {lines}").format(lines=str(self.line_numbers)))

        if not self.datamodel or not self.datamodel.project:
            raise CommandError(_("No project data"), command=self)

        project : SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise CommandError(_("No subtitles"), command=self)

        self.deletions = project.subtitles.DeleteLines(self.line_numbers)

        if not self.deletions:
            raise CommandError(_("No lines were deleted"), command=self)

        # Update the viewmodel. Priginal and translated lines are currently linked, deleting one means deleting both
        model_update = self.AddModelUpdate()
        for deletion in self.deletions:
            scene_number, batch_number, originals, translated = deletion
            for line in originals:
                model_update.lines.remove((scene_number, batch_number, line.number))

            batch = project.subtitles.GetBatch(scene_number, batch_number)
            if batch.errors:
                validator = SubtitleValidator(self.datamodel.project_options)
                validator.ValidateBatch(batch)
                model_update.batches.update((scene_number, batch_number), {'errors': batch.errors})

        return True

    def undo(self):
        if not self.deletions:
            raise CommandError(_("No deletions to undo"), command=self)
        
        if not self.datamodel or not self.datamodel.project:
            raise CommandError(_("No project data"), command=self)

        logging.info(_("Restoring deleted lines"))
        project : SubtitleProject = self.datamodel.project
        subtitles = project.subtitles

        model_update = self.AddModelUpdate()

        for scene_number, batch_number, deleted_originals, deleted_translated in self.deletions:
            batch : SubtitleBatch = subtitles.GetBatch(scene_number, batch_number)
            batch.InsertLines(deleted_originals, deleted_translated)

            for line in deleted_originals:
                translated : SubtitleLine|None = next((translated for translated in deleted_translated if translated.number == line.number), None)
                if translated:
                    line.translated = translated

                model_update.lines.add((scene_number, batch_number, line.number), line)

        return True