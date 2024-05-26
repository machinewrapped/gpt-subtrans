from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator

import logging

from PySubtitle.SubtitleValidator import SubtitleValidator

#############################################################

class ReparseTranslationsCommand(Command):
    """
    Ask the translator to reparse the translation for selected batches
    """
    def __init__(self, batch_numbers : list[(int,int)], line_numbers : list[int], datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.batch_numbers = batch_numbers
        self.line_numbers = line_numbers

    def execute(self):
        logging.info(f"Reparse batches {','.join(str(x) for x in self.batch_numbers)}")

        if not self.datamodel.project:
            raise CommandError("Unable to reparse batches because project is not set on datamodel", command=self)

        project : SubtitleProject = self.datamodel.project
        options = self.datamodel.project_options
        translation_provider = self.datamodel.translation_provider

        translator = SubtitleTranslator(options, translation_provider)
        validator = SubtitleValidator(options)

        model_update = self.AddModelUpdate()
        for scene_number, batch_number in self.batch_numbers:
            try:
                batch : SubtitleBatch = project.ReparseBatchTranslation(translator, scene_number, batch_number, line_numbers=self.line_numbers)

                validator.ValidateBatch(batch)

                model_update.batches.update((scene_number, batch_number), {
                    'summary' : batch.summary,
                    'errors' : batch.errors,
                    'lines' : { line.number : { 'translation' : line.text } for line in batch.translated if line.number }
                })

            except Exception as e:
                raise CommandError(f"Error reparsing scene {scene_number} batch {batch_number}: {e}", command=self)

        project.UpdateProjectFile()

        return True

