from copy import deepcopy
import unittest

import regex

from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Options import Options
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleBatcher import SubtitleBatcher
from PySubtitle.SubtitleError import TranslationError
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationPrompt import TranslationPrompt
from PySubtitle.TranslationProvider import TranslationProvider

class SubtitleTestCase(unittest.TestCase):
    def __init__(self, methodName: str = "runTest", custom_options : dict = None) -> None:
        super().__init__(methodName)

        options = {
            'provider': 'Dummy Provider',
            'provider_options': { 'Dummy Provider' : {} },
            'target_language': 'English',
            'scene_threshold': 60.0,
            'min_batch_size': 10,
            'max_batch_size': 20,
            'preprocess_subtitles': False,
            'postprocess_translation': False,
            'project': 'test',
            'retry_on_error': False,
            'stop_on_error': True
        }

        if custom_options:
            options.update(custom_options)

        self.options = Options(options)

    def _assert_same_as_reference(self, subtitles : SubtitleFile, reference_subtitles: SubtitleFile):
        """
        Assert that the current state of the subtitles is identical to the reference datamodel
        """
        for scene_number in range(1, len(subtitles.scenes) + 1):
            for batch_number in range(1, len(subtitles.GetScene(scene_number).batches) + 1):
                batch = subtitles.GetBatch(scene_number, batch_number)
                reference_batch = reference_subtitles.GetBatch(scene_number, batch_number)

                self._assert_same_as_reference_batch(batch, reference_batch)

    def _assert_same_as_reference_batch(self, batch : SubtitleBatch, reference_batch : SubtitleBatch):
        """
        Assert that the current state of the batch is identical to the reference batch
        """
        self.assertEqual(len(batch.originals), len(reference_batch.originals))
        self.assertEqual(len(batch.translated), len(reference_batch.translated))

        self.assertSequenceEqual([ line.text for line in batch.originals ], [ line.text for line in reference_batch.originals ])
        self.assertSequenceEqual([ line.text for line in batch.translated ], [ line.text for line in reference_batch.translated ])
        self.assertSequenceEqual([ line.start for line in batch.originals ], [ line.start for line in reference_batch.originals ])
        self.assertSequenceEqual([ line.end for line in batch.originals ], [ line.end for line in reference_batch.originals ])


def PrepareSubtitles(subtitle_data : dict, key : str = 'original') -> SubtitleFile:
    """
    Prepares a SubtitleFile object from subtitle data.
    """
    subtitles : SubtitleFile = SubtitleFile()
    subtitles.LoadSubtitlesFromString(subtitle_data[key])
    subtitles.UpdateProjectSettings(subtitle_data)
    return subtitles

def AddTranslations(subtitles : SubtitleFile, subtitle_data : dict, key : str = 'translated'):
    """
    Adds translations to the subtitles.
    """
    translated_file = PrepareSubtitles(subtitle_data, key)
    subtitles.translated = translated_file.originals

    for scene in subtitles.scenes:
        for batch in scene.batches:
            line_numbers = [ line.number for line in batch.originals ]
            batch_translated = [ line for line in subtitles.translated if line.number in line_numbers ]
            batch.translated = batch_translated

            for line in batch.originals:
                line.translated = next((l for l in batch_translated if l.number == line.number), None)
                line.translation = line.translated.text if line.translated else None

def CreateTestDataModel(test_data : dict, options : Options = None) -> ProjectDataModel:
    """
    Creates a ProjectDataModel from test data.
    """
    file : SubtitleFile = PrepareSubtitles(test_data, 'original')
    datamodel = ProjectDataModel(options = options)
    datamodel.project = SubtitleProject(options, file)
    return datamodel

def CreateTestDataModelBatched(test_data : dict, options : Options = None) -> ProjectDataModel:
    """
    Creates a SubtitleBatcher from test data.
    """
    datamodel : ProjectDataModel = CreateTestDataModel(test_data, options)
    subtitles : SubtitleFile = datamodel.project.subtitles
    batcher = SubtitleBatcher(options.GetSettings())
    subtitles.AutoBatch(batcher)

    if 'translated' in test_data:
        AddTranslations(subtitles, test_data, 'translated')

    return datamodel

def AddResponsesFromMap(subtitles : SubtitleFile, test_data : dict):
    """
    Add translator responses to the subtitles if test_data has a response map.
    """
    for prompt, response_text in test_data.get('response_map', []).items():
        # Find scene and batch number from the prompt, e.g. "Translate scene 1 batch 1"
        re_match = regex.match(r"Translate scene (\d+) batch (\d+)", prompt)
        scene_number = int(re_match.group(1))
        batch_number = int(re_match.group(2))
        batch = subtitles.GetBatch(scene_number, batch_number)
        batch.translation = Translation({'text': response_text})

class DummyProvider(TranslationProvider):
    name = "Dummy Provider"

    def __init__(self, data : dict):
        super().__init__("Dummy Provider", {
            "model": "dummy",
            "data": data,
        })

    def GetTranslationClient(self, settings : dict) -> TranslationClient:
        client_settings : dict = deepcopy(self.settings)
        client_settings.update(settings)
        return DummyTranslationClient(settings=client_settings)

class DummyTranslationClient(TranslationClient):
    def __init__(self, settings : dict):
        super().__init__(settings)
        self.data = settings.get('data', {})
        self.response_map = self.data.get('response_map', {})

    def BuildTranslationPrompt(self, dummy_prompt : str, instructions : str, lines : list, context : dict):
        """
        Validate parameters and generate a basic dummy prompt
        """
        if not instructions:
            raise TranslationError("Translator did not receive instructions")

        if not lines:
            raise TranslationError("Translator did not receive lines")

        if not context:
            raise TranslationError("Translator did not receive context")

        if not context.get('movie_name'):
            raise TranslationError("Translator did not receive movie name")

        if not context.get('description'):
            raise TranslationError("Translator did not receive description")

        names = context.get('names', None)
        if not names:
            raise TranslationError("Translator did not receive name list")

        expected_names = self.data.get('names')
        if len(names) < len(expected_names):
            raise TranslationError("Translator did not receive the expected number of names")

        scene_number = context.get('scene_number')
        batch_number = context.get('batch_number')
        dummy_prompt = f"Translate scene {scene_number} batch {batch_number}"

        prompt = TranslationPrompt(dummy_prompt, False)
        prompt.prompt_template = "{prompt}"
        prompt.supports_system_prompt = True
        prompt.GenerateMessages(instructions, lines, context)

        return prompt

    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        for user_prompt, text in self.response_map.items():
            if user_prompt == prompt.user_prompt:
                text = text.replace("\\n", "\n")
                return Translation({'text': text})
