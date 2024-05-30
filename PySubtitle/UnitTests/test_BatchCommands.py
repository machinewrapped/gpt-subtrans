from GUI.Commands.BatchSubtitlesCommand import BatchSubtitlesCommand

from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Helpers.TestCases import CreateTestDataModel, SubtitleTestCase
from PySubtitle.Helpers.Tests import log_input_expected_result, log_test_name
from PySubtitle.Options import Options
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.UnitTests.TestData.chinese_dinner import chinese_dinner_data

class BatchCommandTests(SubtitleTestCase):
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

    batch_command_test_cases = [
        {
            'data': chinese_dinner_data,
            'expected_scene_count': 4,
            'expected_scene_sizes': [2, 2, 1, 1],
            'expected_scene_linecounts': [30, 25, 6, 3],
            'expected_scene_batch_sizes': [[14, 16], [12, 13], [6], [3]],
        }
    ]

    def test_BatchCommands(self):
        for test_case in self.batch_command_test_cases:
            data = test_case['data']
            log_test_name(f"Testing batch command on {data.get('movie_name')}")

            datamodel : ProjectDataModel = CreateTestDataModel(data, self.options)
            file : SubtitleFile = datamodel.project.subtitles

            with self.subTest("BatchSubtitlesCommand"):
                self.BatchSubtitlesCommandTest(file, datamodel, test_case)


    def BatchSubtitlesCommandTest(self, file : SubtitleFile, datamodel : ProjectDataModel, test_data : dict):
        expected_scene_count = test_data['expected_scene_count']
        expected_scene_sizes = test_data['expected_scene_sizes']
        expected_scene_linecounts = test_data['expected_scene_linecounts']
        expected_scene_batch_sizes = test_data['expected_scene_batch_sizes']

        batch_command = BatchSubtitlesCommand(datamodel.project, datamodel.project_options)
        self.assertTrue(batch_command.execute())
        self.assertTrue(len(file.scenes) > 0)

        log_input_expected_result("Scene count", expected_scene_count, len(file.scenes))
        self.assertEqual(len(file.scenes), 4)

        scene_sizes = [scene.size for scene in file.scenes]
        scene_linecounts = [scene.linecount for scene in file.scenes]
        scene_batch_sizes = [[batch.size for batch in scene.batches] for scene in file.scenes]

        log_input_expected_result("Scene size", expected_scene_sizes, scene_sizes)
        log_input_expected_result("Scene line count", expected_scene_linecounts, scene_linecounts)
        log_input_expected_result("Scene batch sizes", expected_scene_batch_sizes, scene_batch_sizes)

        self.assertEqual(scene_sizes, expected_scene_sizes)
        self.assertEqual(scene_linecounts, expected_scene_linecounts)
        self.assertSequenceEqual(scene_batch_sizes, expected_scene_batch_sizes)

