import logging

from GUI.Command import Command, CommandError, UndoError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleFile import SubtitleFile

class MergeScenesCommand(Command):
    """
    Combine multiple scenes into one
    """
    def __init__(self, scene_numbers : list[int], datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_numbers = sorted(scene_numbers)

    def execute(self):
        logging.info(f"Merging scenes {','.join(str(x) for x in self.scene_numbers)}")

        subtitles : SubtitleFile = self.datamodel.project.subtitles

        if len(self.scene_numbers) < 2:
            raise CommandError("Cannot merge less than two scenes", command=self)

        later_scenes = [scene.number for scene in subtitles.scenes if scene.number > self.scene_numbers[-1]]

        merged_scene = subtitles.MergeScenes(self.scene_numbers)

        model_update = self.AddModelUpdate()
        for new_number, current_number in enumerate(later_scenes, start=merged_scene.number + 1):
            model_update.scenes.update(current_number, { 'number' : new_number })

        model_update.scenes.replace(merged_scene.number, merged_scene)
        model_update.scenes.removals = self.scene_numbers[1:]



        return True