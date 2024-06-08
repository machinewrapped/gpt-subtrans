from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject

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

        self._swap_text_and_translation()

        return True

    def undo(self):
        logging.info(f"Undoing swap text and translations")
        self._swap_text_and_translation()
        return True

    def _swap_text_and_translation(self):
        project : SubtitleProject = self.datamodel.project
        subtitles : SubtitleFile = project.subtitles
        batch = subtitles.GetBatch(self.scene_number, self.batch_number)

        # Swap original and translated text (only in the viewmodel)
        model_update = self.AddModelUpdate()
        for original, translated in zip(batch.originals, batch.translated):
            if original and translated:
                model_update.lines.update((batch.scene, batch.number, original.number), { 'text': translated.text, 'translation': original.text } )

