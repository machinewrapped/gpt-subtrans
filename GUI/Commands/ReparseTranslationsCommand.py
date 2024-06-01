from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleFile import SubtitleFile
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
        self.undo_data = []

    def execute(self):
        logging.info(f"Reparse batches {','.join(str(x) for x in self.batch_numbers)}")

        if not self.datamodel.project:
            raise CommandError("Unable to reparse batches because project is not set", command=self)

        project : SubtitleProject = self.datamodel.project
        subtitles : SubtitleFile = project.subtitles
        options = self.datamodel.project_options
        translation_provider = self.datamodel.translation_provider

        translator = SubtitleTranslator(options, translation_provider)
        validator = SubtitleValidator(options)

        for scene_number, batch_number in self.batch_numbers:
            try:
                batch : SubtitleBatch = subtitles.GetBatch(scene_number, batch_number)
                self.undo_data.append( (scene_number, batch_number, self._generate_undo_data(batch, self.line_numbers)) )

                project.ReparseBatchTranslation(translator, scene_number, batch_number, line_numbers=self.line_numbers)

                validator.ValidateBatch(batch)

                model_update = self.AddModelUpdate()
                model_update.batches.update((scene_number, batch_number), {
                    'summary' : batch.summary,
                    'errors' : batch.errors,
                    'lines' : { line.number : { 'translation' : line.text } for line in batch.translated if line.number }
                })

            except Exception as e:
                raise CommandError(f"Error reparsing scene {scene_number} batch {batch_number}: {e}", command=self)

        project.UpdateProjectFile()

        return True

    def _generate_undo_data(self, batch : SubtitleBatch, line_numbers : list[int] = None):
        lines = [line for line in batch.translated if line.number in line_numbers] if line_numbers is not None else batch.translated

        return {
            'summary' : batch.summary,
            'lines' : { line.number : line.text for line in lines }
        }

    def undo(self):
        project : SubtitleProject = self.datamodel.project
        subtitles : SubtitleFile = project.subtitles

        for scene_number, batch_number, undo_data in self.undo_data:
            batch : SubtitleBatch = subtitles.GetBatch(scene_number, batch_number)
            summary = undo_data.get('summary', None)
            undo_lines = undo_data['lines']

            if summary:
                batch.summary = summary

            for line in batch.translated:
                undo_translated = undo_lines.get(line.number, None)
                if undo_translated:
                    line.text = undo_translated

        return True