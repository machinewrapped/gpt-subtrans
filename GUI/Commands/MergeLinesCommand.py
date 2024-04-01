from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectSelection import ProjectSelection
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleProject import SubtitleProject

import logging

class MergeLinesCommand(Command):
    """
    Merge one or several lines together
    """
    def __init__(self, selection : ProjectSelection, datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.selection = selection

    def execute(self):
        lines = [line.number for line in self.selection.selected_lines]

        if lines:
            logging.info(f"Merging lines {str(lines)}")
        else:
            raise CommandError("No lines selected to merge", command=self)

        project : SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise CommandError("No subtitles", command=self)

        selected = self.selection.GetHierarchy()

        if selected:
            project.subtitles.MergeLines(selected)

            for scene_number in selected.keys():
                batches_to_update : list[SubtitleBatch] = [ project.subtitles.GetBatch(scene_number, batch_number) for batch_number in selected[scene_number].keys() ]

                for batch in batches_to_update:
                    self.model_update.batches.replace((scene_number, batch.number), batch)

        return True

    def undo(self):
        # TODO: Really need to implement undo for this!
        raise CommandError("Undo not supported for MergeLinesCommand yet")