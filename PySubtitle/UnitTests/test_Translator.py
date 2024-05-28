from copy import deepcopy
import unittest

from PySubtitle.Helpers.Tests import PrepareSubtitles, log_info, log_input_expected_result, log_test_name
from PySubtitle.Options import Options
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleBatcher import SubtitleBatcher
from PySubtitle.SubtitleError import TranslationError
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleScene import SubtitleScene
from PySubtitle.SubtitleTranslator import SubtitleTranslator
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationPrompt import TranslationPrompt
from PySubtitle.TranslationProvider import TranslationProvider

from PySubtitle.UnitTests.TestData.chinese_dinner import chinese_dinner_data

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


class SubtitleTranslatorTests(unittest.TestCase):
    options = Options({
        'target_language': 'English',
        'scene_threshold': 60.0,
        'max_batch_size': 100,
        'preprocess_subtitles': False,
        'postprocess_translation': False,
        'project': 'test',
        'retry_on_error': False,
        'stop_on_error': True
    })

    def test_SubtitleTranslator(self):
        log_test_name("Subtitle translator tests")

        test_data = [ chinese_dinner_data ]

        for data in test_data:
            log_test_name(f"Testing translation of {data.get('movie_name')}")

            provider = DummyProvider(data=data)

            originals : SubtitleFile = PrepareSubtitles(data, 'original')
            reference : SubtitleFile = PrepareSubtitles(data, 'translated')

            self.assertEqual(originals.linecount, reference.linecount)

            batcher = SubtitleBatcher(self.options)
            originals.AutoBatch(batcher)
            reference.AutoBatch(batcher)

            self.assertEqual(len(originals.scenes), len(reference.scenes))

            for i in range(len(originals.scenes)):
                self.assertEqual(originals.scenes[i].size, reference.scenes[i].size)
                self.assertEqual(originals.scenes[i].linecount, reference.scenes[i].linecount)

            translator = SubtitleTranslator(self.options, translation_provider=provider)
            translator.events.batch_translated += lambda batch: self.validate_batch(batch, original=originals, reference=reference)
            translator.events.scene_translated += lambda scene: self.validate_scene(scene, original=originals, reference=reference)

            translator.TranslateSubtitles(originals)

    def validate_batch(self, batch : SubtitleBatch, original : SubtitleFile, reference : SubtitleFile):
        log_info(f"Validating scene {batch.scene} batch {batch.number}")
        log_info(f"Summary: {batch.summary}")
        self.assertIsNotNone(batch.summary)

        log_info(f"Scene: {batch.context.get('scene')}")
        self.assertIsNotNone(batch.context.get('scene'))

        self.assertEqual(batch.context.get('movie_name'), original.movie_name)
        self.assertEqual(batch.context.get('description'), original.settings.get('description'))
        self.assertSequenceEqual(batch.context.get('names'), original.settings.get('names'))

        reference_batch = reference.GetBatch(batch.scene, batch.number)

        log_input_expected_result("Line count", reference_batch.size, batch.size)
        self.assertEqual(reference_batch.size, batch.size)

        self.assertEqual(batch.first_line_number, reference_batch.first_line_number)
        self.assertEqual(batch.last_line_number, reference_batch.last_line_number)
        self.assertEqual(batch.start, reference_batch.start)
        self.assertEqual(batch.end, reference_batch.end)

        original_batch = original.GetBatch(batch.scene, batch.number)
        for i in range(len(batch.originals)):
            self.assertEqual(original_batch.originals[i], batch.originals[i])
            self.assertEqual(reference_batch.originals[i], batch.translated[i])

    def validate_scene(self, scene : SubtitleScene, original : SubtitleFile, reference : SubtitleFile):
        log_info(f"Validating scene {scene.number}")
        log_info(f"Summary: {scene.summary}")
        self.assertIsNotNone(scene.summary)

        reference_scene = reference.GetScene(scene.number)
        log_input_expected_result("Batch count", reference_scene.size, scene.size)
        log_input_expected_result("Line count", reference_scene.linecount, scene.linecount)

        self.assertEqual(reference_scene.size, scene.size)
        self.assertEqual(reference_scene.linecount, scene.linecount)


    def test_PostProcessTranslation(self):
        log_test_name("Post process translation tests")

        test_data = [ chinese_dinner_data ]

        for data in test_data:
            log_test_name(f"Testing translation of {data.get('movie_name')}")

            provider = DummyProvider(data=data)

            originals : SubtitleFile = PrepareSubtitles(data, 'original')
            reference : SubtitleFile = PrepareSubtitles(data, 'translated')

            self.assertEqual(originals.linecount, reference.linecount)

            batcher = SubtitleBatcher(self.options)
            originals.AutoBatch(batcher)
            reference.AutoBatch(batcher)

            self.assertEqual(len(originals.scenes), len(reference.scenes))

            options = deepcopy(self.options)
            options.add('postprocess_translation', True)
            translator = SubtitleTranslator(options, translation_provider=provider)
            translator.TranslateSubtitles(originals)

            differences = sum(1 if reference.originals[i] != originals.translated[i] else 0 for i in range(len(originals.originals)))
            unchanged = sum (1 if reference.originals[i] == originals.translated[i] else 0 for i in range(len(originals.originals)))

            expected_differences = data['expected_postprocess_differences']
            expected_unchanged = data['expected_postprocess_unchanged']

            log_input_expected_result("Differences", expected_differences, differences)
            self.assertEqual(differences, expected_differences)

            log_input_expected_result("Unchanged", expected_unchanged, unchanged)
            self.assertEqual(unchanged, expected_unchanged)


