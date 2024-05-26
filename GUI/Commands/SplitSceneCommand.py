from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleProject import SubtitleProject

import logging

class SplitSceneCommand(Command):
    def __init__(self, scene_number : int, batch_number : int, datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_number = batch_number

    def execute(self):
        logging.info(f"Splitting batch {str(self.scene_number)} at batch {str(self.batch_number)}")

        project : SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise CommandError("No subtitles", command=self)

        scene = project.subtitles.GetScene(self.scene_number)
        if not scene:
            raise CommandError(f"Cannot split scene {self.scene_number} because it doesn't exist", command=self)

        last_batch = scene.batches[-1].number

        project.subtitles.SplitScene(self.scene_number, self.batch_number)

        model_update = self.AddModelUpdate()
        for scene_number in range(self.scene_number + 1, len(project.subtitles.scenes)):
             model_update.scenes.update(scene_number, { 'number' : scene_number + 1})

        for batch_removed in range(self.batch_number, last_batch + 1):
            model_update.batches.remove((self.scene_number, batch_removed))

        model_update.scenes.add(self.scene_number + 1, project.subtitles.GetScene(self.scene_number + 1))

        return True

    def undo(self):
        project: SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise CommandError("No subtitles", command=self)

        try:
            project.subtitles.MergeScenes([self.scene_number, self.scene_number + 1])
            scene_numbers = [self.scene_number, self.scene_number + 1]
            merged_scene = project.subtitles.MergeScenes(scene_numbers)

            model_update = self.AddModelUpdate()
            model_update.scenes.replace(self.scene_number, merged_scene)
            model_update.scenes.remove(self.scene_number + 1)

            later_scenes = [scene for scene in project.subtitles.scenes if scene.number > self.scene_number]
            for scene in later_scenes:
                model_update.scenes.update(scene.number, { 'number' : scene.number - 1 })

            return True

        except Exception as e:
            raise CommandError(f"Unable to undo SplitScene command: {str(e)}", command=self)