from copy import deepcopy
import unittest

from GUI.Commands.DeleteLinesCommand import DeleteLinesCommand
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Helpers.TestCases import CreateTestDataModelBatched, SubtitleTestCase
from PySubtitle.Helpers.Tests import log_info, log_input_expected_result, log_test_name
from PySubtitle.Options import Options
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.UnitTests.TestData.chinese_dinner import chinese_dinner_data

class DeleteLinesCommandTest(SubtitleTestCase):
    options = Options({
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
    })

    delete_lines_test_cases = [
        {
            'batch_number': (1,1),
            'lines_to_delete': [1,2,3],
            'expected_batch_size': 11,
            'expected_line_numbers': [4,5,6,7,8,9,10,11,12,13,14]
        },
        {
            'batch_number': (1,1),
            'lines_to_delete': [9,10],
            'expected_batch_size': 12,
            'expected_line_numbers': [1,2,3,4,5,6,7,8,11,12,13,14]
        },
        {
            'batch_number': (1,1),
            'lines_to_delete': [14],
            'expected_batch_size': 13,
            'expected_line_numbers': [1,2,3,4,5,6,7,8,9,10,11,12,13]
        }
    ]


    def test_DeleteLinesCommand(self):
        log_test_name("DeleteLinesCommand")

        data = deepcopy(chinese_dinner_data)

        datamodel : ProjectDataModel = CreateTestDataModelBatched(data, options=self.options)
        subtitles: SubtitleFile = datamodel.project.subtitles

        for test_case in self.delete_lines_test_cases:
            scene_number, batch_number = test_case['batch_number']
            lines_to_delete = test_case['lines_to_delete']

            expected_batch_size = test_case['expected_batch_size']
            expected_line_numbers = test_case['expected_line_numbers']

            batch = subtitles.GetBatch(scene_number, batch_number)

            initial_batch_size = len(batch.originals)
            initial_line_numbers = [line.number for line in batch.originals]

            log_info(f"Deleting lines {lines_to_delete} from batch {scene_number}.{batch_number}")

            self.assertTrue(all([any([line.number == line_number for line in batch.originals]) for line_number in lines_to_delete]))

            command = DeleteLinesCommand(lines_to_delete, datamodel=datamodel)
            self.assertTrue(command.execute())

            log_input_expected_result("After Delete", expected_batch_size, len(batch.originals))
            self.assertEqual(len(batch.originals), expected_batch_size)
            self.assertSequenceEqual([line.number for line in batch.originals], expected_line_numbers)

            self.assertTrue(command.can_undo)
            self.assertTrue(command.undo())

            log_input_expected_result("After Undo", initial_batch_size, len(batch.originals))
            self.assertEqual(len(batch.originals), initial_batch_size)
            self.assertSequenceEqual([line.number for line in batch.originals], initial_line_numbers)


