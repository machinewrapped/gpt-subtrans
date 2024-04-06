#############################################################

from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleProject import SubtitleProject


import logging


class MergeScenesCommand(Command):
    """
    Combine multiple scenes into one
    """
    def __init__(self, scene_numbers : list[int], datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_numbers = sorted(scene_numbers)

    def execute(self):
        logging.info(f"Merging scenes {','.join(str(x) for x in self.scene_numbers)}")

        project : SubtitleProject = self.datamodel.project

        if len(self.scene_numbers) > 1:
            project.subtitles.MergeScenes(self.scene_numbers)

        #TODO: incremental updates to the data/view model
        self.datamodel.CreateViewModel()

        return True