from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Options import Options
from PySubtitle.SubtitleBatcher import CreateSubtitleBatcher, SubtitleBatcher
from PySubtitle.SubtitleProject import SubtitleProject

import logging

class BatchSubtitlesCommand(Command):
    """
    Attempt to partition subtitles into scenes and batches based on thresholds and limits.
    """
    def __init__(self, project : SubtitleProject, options : Options):
        super().__init__()
        self.project : SubtitleProject = project
        self.options : Options = options

    def execute(self):
        logging.info("Executing BatchSubtitlesCommand")

        project : SubtitleProject = self.project

        if not project or not project.subtitles:
            logging.error("No subtitles to batch")

        batcher : SubtitleBatcher = CreateSubtitleBatcher(self.options)
        project.subtitles.AutoBatch(batcher)

        project.WriteProjectFile()

        self.datamodel : ProjectDataModel = self.datamodel or ProjectDataModel(project)
        self.datamodel.CreateViewModel()
        return True

    def undo(self):
        # Do we flatten, or do we cache the previous batches?
        pass