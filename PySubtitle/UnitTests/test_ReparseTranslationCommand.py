from copy import deepcopy

from GUI.Commands.ReparseTranslationsCommand import ReparseTranslationsCommand
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Helpers.TestCases import CreateTestDataModelBatched, AddResponsesFromMap, SubtitleTestCase
from PySubtitle.Helpers.Tests import log_info, log_input_expected_result, log_test_name
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.UnitTests.TestData.chinese_dinner import chinese_dinner_data

class ReparseTranslationsCommandTest(SubtitleTestCase):
    def __init__(self, methodName):
        super().__init__(methodName, custom_options={
            'max_batch_size': 100,
        })

    reparse_test_cases = [
        {
            'data': deepcopy(chinese_dinner_data),
            'batch_numbers': [(1,1), (2,1), (3,1), (4,1)],
            'line_numbers': None
        },
        {
            'data': deepcopy(chinese_dinner_data),
            'batch_numbers': [(2,1)],
            'line_numbers': [41,42,43,44,45]
        }
    ]

    def test_ReparseTranslationsCommand(self):
        log_test_name("ReparseTranslationsCommand")

        for test_case in self.reparse_test_cases:
            data = test_case['data']
            batch_numbers = test_case['batch_numbers']
            line_numbers = test_case['line_numbers']

            # Create a reference data model with translations
            reference_datamodel : ProjectDataModel = CreateTestDataModelBatched(data, options=self.options)
            reference_subtitles = reference_datamodel.project.subtitles

            # Create a test data model with translated lines replaced by a copy of the original lines
            test_data = deepcopy(data)
            test_data['translated'] = test_data['original']
            test_datamodel : ProjectDataModel = CreateTestDataModelBatched(test_data, options=self.options)
            test_subtitles: SubtitleFile = test_datamodel.project.subtitles

            # Add the translator responses to the test data model
            AddResponsesFromMap(test_subtitles, test_data)

            command = ReparseTranslationsCommand(batch_numbers, None, datamodel=test_datamodel)
            self.assertTrue(command.execute())

            for scene_number, batch_number in batch_numbers:
                batch = test_subtitles.GetBatch(scene_number, batch_number)
                self.assertIsNotNone(batch)
                self.assertIsNotNone(batch.translation)

                reference_batch = reference_subtitles.GetBatch(scene_number, batch_number)
                self.assertIsNotNone(reference_batch)

                if line_numbers:
                    for line in batch.originals:
                        reference_line = reference_batch.GetTranslatedLine(line.number) if line.number in line_numbers else batch.GetOriginalLine(line.number)
                        self.assertIsNotNone(reference_line)
                        self.assertEqual(line, reference_line)
                else:
                    self._assert_same_as_reference_batch(batch, reference_batch)

            # Verify that undoing the command stack restores the original state
            self.assertTrue(command.can_undo)
            self.assertTrue(command.undo())

            for scene_number, batch_number in batch_numbers:
                batch = test_subtitles.GetBatch(scene_number, batch_number)

                for line in batch.originals:
                    line_number = line.number
                    translated_line = batch.GetTranslatedLine(line_number)

                    self.assertIsNotNone(translated_line)
                    self.assertEqual(line, translated_line)

