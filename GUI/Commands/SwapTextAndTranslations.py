from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleScene import SubtitleScene

import logging

class SwapTextAndTranslations(Command):
    """
    Test class for model updates
    """
    def __init__(self, scene_number : int, batch_number : int, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_number = batch_number

    def execute(self):
        logging.info(f"Swapping text and translations in scene {self.scene_number} batch {self.batch_number}")
        if not self.datamodel.project:
            raise CommandError("Unable to translate scene because project is not set on datamodel", command=self)

        project : SubtitleProject = self.datamodel.project
        file : SubtitleFile = project.subtitles
        scene : SubtitleScene = file.GetScene(self.scene_number)
        batch : SubtitleBatch = scene.GetBatch(self.batch_number)

        # Swap original and translated text (only in the viewmodel)
        for original, translated in zip(batch.originals, batch.translated):
            if original and translated:
                self.model_update.lines.update((scene.number, batch.number, original.number), { 'text': translated.text, 'translation': original.text } )

        return True