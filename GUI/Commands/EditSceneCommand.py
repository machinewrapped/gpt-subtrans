import logging
from copy import deepcopy
from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleScene import SubtitleScene

class EditSceneCommand(Command):
    def __init__(self, scene_number : int, edit : dict, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.edit = deepcopy(edit)
        self.undo_data = None

    def execute(self):
        logging.debug(f"Editing scene {self.scene_number}")

        subtitles : SubtitleFile = self.datamodel.project.subtitles
        if not subtitles:
            raise CommandError("Unable to edit scene because datamodel is invalid", command=self)

        if not isinstance(self.edit, dict):
            raise CommandError("Edit data must be a dictionary", command=self)

        with subtitles.lock:
            scene : SubtitleScene = subtitles.GetScene(self.scene_number)
            if not scene:
                raise CommandError(f"Scene {self.scene_number} not found", command=self)

            self.undo_data = {
                "summary": scene.summary,
            }

            scene.summary = self.edit.get('summary', scene.summary)

            self._update_viewmodel(scene)

        return True

    def undo(self):
        logging.debug(f"Undoing edit scene {self.scene_number}")

        subtitles : SubtitleFile = self.datamodel.project.subtitles

        with subtitles.lock:
            scene = subtitles.GetScene(self.scene_number)
            if not scene:
                raise CommandError(f"Scene {self.scene_number} not found", command=self)

            scene.summary = self.undo_data.get('summary', scene.summary)

            self._update_viewmodel(scene)

        return True

    def _update_viewmodel(self, scene):
        viewmodel_update = self.AddModelUpdate()
        viewmodel_update.scenes.update(self.scene_number, { 'summary': scene.summary })
