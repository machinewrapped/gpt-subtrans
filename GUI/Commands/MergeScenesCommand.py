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

        # Remove the previously merged batches from the merged scene
        scene_to_split = subtitles.GetScene(self.scene_numbers[0])
        for batch_number in [batch.number for batch in scene_to_split.batches[self.scene_sizes[0]:]]:
            model_update.batches.remove((scene_to_split.number, batch_number))

        # Renumber later scenes to their original numbers
        later_scenes = [scene.number for scene in subtitles.scenes if scene.number > self.scene_numbers[0]]
        later_scene_start_number = self.scene_numbers[-1] + 1
        for scene_number, current_number in enumerate(later_scenes, start=later_scene_start_number):
            model_update.scenes.update(current_number, { 'number' : scene_number })

        # Split the merged scene according to the saved scene sizes and add the new scenes to the viewmodel
        for scene_number, scene_size in enumerate(self.scene_sizes[:-1], start=self.scene_numbers[0]):
            subtitles.SplitScene(scene_number, scene_size + 1)
            model_update.scenes.add(scene_number + 1, subtitles.GetScene(scene_number + 1))

        return True