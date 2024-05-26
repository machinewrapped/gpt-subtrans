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
        self.scene_sizes = []

    def execute(self):
        logging.info(f"Merging scenes {','.join(str(x) for x in self.scene_numbers)}")

        subtitles : SubtitleFile = self.datamodel.project.subtitles

        if len(self.scene_numbers) < 2:
            raise CommandError("Cannot merge less than two scenes", command=self)

        scenes_to_merge = [ subtitles.GetScene(scene_number) for scene_number in self.scene_numbers ]
        self.scene_sizes = [ scene.size for scene in scenes_to_merge ]

        later_scenes = [scene.number for scene in subtitles.scenes if scene.number > self.scene_numbers[-1]]

        merged_scene = subtitles.MergeScenes(self.scene_numbers)

        model_update = self.AddModelUpdate()
        for new_number, current_number in enumerate(later_scenes, start=merged_scene.number + 1):
            model_update.scenes.update(current_number, { 'number' : new_number })

        model_update.scenes.replace(merged_scene.number, merged_scene)
        model_update.scenes.removals = self.scene_numbers[1:]

        self.can_undo = True
        return True

    def undo(self):
        """
        Split the scene recursively using the saved scene sizes
        """
        if not self.scene_sizes:
            raise UndoError("Cannot undo merge, scene sizes were not saved", command=self)

        subtitles : SubtitleFile = self.datamodel.project.subtitles

        model_update = self.AddModelUpdate()
        model_update.scenes.remove(self.scene_numbers[0])

        later_scenes = [scene.number for scene in subtitles.scenes if scene.number > self.scene_numbers[0]]
        for new_number, current_number in enumerate(later_scenes, start=self.scene_numbers[-1] + 1):
            model_update.scenes.update(current_number, { 'number' : new_number })

        for new_number, scene_size in enumerate(self.scene_sizes[:-1], start=self.scene_numbers[0]):
            subtitles.SplitScene(new_number, scene_size + 1)
            model_update.scenes.add(new_number, subtitles.GetScene(new_number))

        return True