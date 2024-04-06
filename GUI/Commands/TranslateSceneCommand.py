from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ViewModel.ViewModelUpdate import ModelUpdate
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleError import TranslationImpossibleError
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator

import logging

#############################################################

class TranslateSceneCommand(Command):
    """
    Ask the translator to translate a scene (optionally just select batches in the scene)
    """
    def __init__(self, scene_number : int, batch_numbers : list[int] = None, line_numbers : list[int] = None, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.translator = None
        self.scene_number = scene_number
        self.batch_numbers = batch_numbers
        self.line_numbers = line_numbers

    def execute(self):
        if self.batch_numbers:
            logging.info(f"Translating scene number {self.scene_number} batch {','.join(str(x) for x in self.batch_numbers)}")
        else:
            logging.info(f"Translating scene number {self.scene_number}")

        if not self.datamodel.project:
            raise CommandError("Unable to translate scene because project is not set on datamodel", command=self)

        project : SubtitleProject = self.datamodel.project

        options = self.datamodel.project_options
        translation_provider = self.datamodel.translation_provider

        self.translator = SubtitleTranslator(options, translation_provider)

        self.translator.events.batch_translated += self._on_batch_translated

        try:
            scene = project.TranslateScene(self.translator, self.scene_number, batch_numbers=self.batch_numbers, line_numbers=self.line_numbers)

            project.UpdateProjectFile()

        except TranslationImpossibleError as e:
            logging.error(f"Unable to translate scene {self.scene_number}: {e}")
            self.terminal = True
            scene = None

        except Exception as e:
            logging.error(f"Error translating scene {self.scene_number}: {e}")
        
        self.translator.events.batch_translated -= self._on_batch_translated

        if scene:
            self.model_update.scenes.update(scene.number, {
                'summary' : scene.summary
            })

            for batch in scene.batches:
                if batch.translated:
                    if not self.batch_numbers or batch.number in self.batch_numbers:
                        self.model_update.batches.update((scene.number, batch.number), {
                            'summary' : batch.summary,
                            'context' : batch.context,
                            'errors' : batch.errors,
                            'translation': batch.translation,
                            'lines' : { line.number : { 'translation' : line.text } for line in batch.translated }
                        })

        return True

    def on_abort(self):
        if self.translator:
            self.translator.StopTranslating()

    def _on_batch_translated(self, batch : SubtitleBatch):
        # Update viewmodel as each batch is translated 
        if self.datamodel and batch.translated:
            update = ModelUpdate()
            update.batches.update((batch.scene, batch.number), {
                'summary' : batch.summary,
                'context' : batch.context,
                'errors' : batch.errors,
                'translation': batch.translation,
                'prompt': batch.prompt,
                'lines' : { line.number : { 'translation' : line.text } for line in batch.translated if line.number }
            })

            self.datamodel.UpdateViewModel(update)

#############################################################

class TranslateSceneMultithreadedCommand(TranslateSceneCommand):
    """
    A non-blocking version of TranslateSceneCommand
    """
    def __init__(self, scene_number: int, batch_numbers: list[int] = None, line_numbers : list[int] = None, datamodel: ProjectDataModel = None):
        super().__init__(scene_number, batch_numbers, line_numbers, datamodel)
        self.is_blocking = False

