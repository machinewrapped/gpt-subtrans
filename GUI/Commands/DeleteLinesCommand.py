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

        # Update the viewmodel. Currently assumes original and translated lines are deleted together
        for scene_number, batch_number, originals, translated in self.deletions:
            for line in originals:
                self.model_update.lines.remove((scene_number, batch_number, line.number))

        return True

    def undo(self):
        if not self.deletions:
            return True

        logging.info(f"Restoring deleted lines")
        project : SubtitleProject = self.datamodel.project
        subtitles = project.subtitles
        for scene_number, batch_number, deleted_originals, deleted_translated in self.deletions:
            batch = subtitles.GetBatch(scene_number, batch_number)
            batch.InsertLines(deleted_originals, deleted_translated)

