from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectSelection import ProjectSelection
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.SubtitleProject import SubtitleProject

import logging

class DeleteLinesCommand(Command):
    """
    Delete one or several lines
    """
    def __init__(self, line_numbers : list[int], datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.line_numbers = line_numbers
        self.deletions = []

    def execute(self):
        if not self.line_numbers:
            raise CommandError("No lines selected to delete", command=self)

        logging.info(f"Deleting lines {str(self.line_numbers)}")

        project : SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise CommandError("No subtitles", command=self)

        self.deletions = project.subtitles.DeleteLines(self.line_numbers)

        if not self.deletions:
            raise CommandError("No lines were deleted", command=self)

        # Update the viewmodel. Priginal and translated lines are currently linked, deleting one means deleting both
        model_update = self.AddModelUpdate()
        for scene_number, batch_number, originals, translated in self.deletions:
            for line in originals:
                model_update.lines.remove((scene_number, batch_number, line.number))

        self.can_undo = True
        return True

    def undo(self):
        if not self.deletions:
            return True

        logging.info(f"Restoring deleted lines")
        project : SubtitleProject = self.datamodel.project
        subtitles = project.subtitles

        model_update = self.AddModelUpdate()

        for scene_number, batch_number, deleted_originals, deleted_translated in self.deletions:
            batch = subtitles.GetBatch(scene_number, batch_number)
            batch.InsertLines(deleted_originals, deleted_translated)

            for line in deleted_originals:
                deleted_translated = next((line for line in deleted_translated if line.number == line.number), None)
                if deleted_translated:
                    line.translation = deleted_translated.text

                model_update.lines.add((scene_number, batch_number), line)

