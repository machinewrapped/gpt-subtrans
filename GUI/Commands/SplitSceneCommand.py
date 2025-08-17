from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.Helpers.Localization import _

import logging

class SplitSceneCommand(Command):
    def __init__(self, scene_number : int, batch_number : int, datamodel: ProjectDataModel|None = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_number = batch_number

    def execute(self):
        logging.info(_("Splitting batch {scene} at batch {batch}").format(scene=str(self.scene_number), batch=str(self.batch_number)))

        project : SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise CommandError(_("No subtitles"), command=self)

        scene = project.subtitles.GetScene(self.scene_number)
        if not scene:
            raise CommandError(_("Cannot split scene {scene} because it doesn't exist").format(scene=self.scene_number), command=self)

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
            raise CommandError(_("No subtitles"), command=self)

        try:
            scene_numbers = [self.scene_number, self.scene_number + 1]
            later_scenes = [scene.number for scene in project.subtitles.scenes if scene.number > scene_numbers[1]]

            merged_scene = project.subtitles.MergeScenes(scene_numbers)

            # Recombine the split scenes
            model_update = self.AddModelUpdate()
            model_update.scenes.replace(scene_numbers[0], merged_scene)
            model_update.scenes.remove(scene_numbers[1])

            # Renumber the later scenes (must be done after the merge to avoid conflicts)
            renumber_update = self.AddModelUpdate()
            for scene_number in later_scenes:
                renumber_update.scenes.update(scene_number, { 'number' : scene_number - 1 })

            return True

        except Exception as e:
            raise CommandError(_("Unable to undo SplitScene command: {error}").format(error=str(e)), command=self)