from copy import deepcopy
import unittest

from GUI.Commands.BatchSubtitlesCommand import BatchSubtitlesCommand
from GUI.Commands.MergeBatchesCommand import MergeBatchesCommand
from GUI.Commands.MergeScenesCommand import MergeScenesCommand
from GUI.Commands.SplitSceneCommand import SplitSceneCommand
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Helpers.Tests import AddTranslations, CreateTestDataModel, PrepareSubtitles, log_input_expected_result, log_test_name
from PySubtitle.Options import Options
from PySubtitle.SubtitleBatch import SubtitleBatch

from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.UnitTests.TestData.chinese_dinner import chinese_dinner_data

class CommandsTests(unittest.TestCase):
    options = Options({
        'provider': 'Dummy Provider',
        'provider_options': { 'Dummy Provider' : {} },
        'target_language': 'English',
        'scene_threshold': 60.0,
        'max_batch_size': 20,
        'preprocess_subtitles': False,
        'postprocess_translation': False,
        'project': 'test',
        'retry_on_error': False,
        'stop_on_error': True
    })

    command_test_cases = [
        {
            'data': chinese_dinner_data,
            'BatchSubtitlesCommand': {
                'expected_scene_count': 4,
                'expected_scene_sizes': [2, 2, 1, 1],
                'expected_scene_linecounts': [30, 25, 6, 3],
            },
            'tests' : [
                {
                    'command': 'MergeSceneCommandTest',
                    'scene_numbers': [2, 3],
                    'expected_scene_count': 3,
                    'expected_merged_scene_numbers': [1, 2, 3],
                    'expected_merged_linecounts': [30, 31, 3],
                    'expected_merged_scene_batches': [1, 2, 3],
                    'expected_merged_scene_sizes': [3, 3, 2],
                },
                {
                    'command': 'MergeSceneCommandTest',
                    'scene_numbers': [1, 2,3],
                    'expected_scene_count': 2,
                    'expected_merged_scene_numbers': [1, 2],
                    'expected_merged_linecounts': [61, 3],
                    'expected_merged_scene_batches': [1, 2, 3, 4, 5],
                    'expected_merged_scene_sizes': [5, 2],
                },
                {
                    'command': 'MergeSceneCommandTest',
                    'scene_numbers': [1, 2, 3, 4],
                    'expected_scene_count': 1,
                    'expected_merged_scene_numbers': [1],
                    'expected_merged_linecounts': [64],
                    'expected_merged_scene_batches': [1, 2, 3, 4, 5, 6],
                    'expected_merged_scene_sizes': [7],
                },
                {
                    'command': 'MergeBatchesCommandTest',
                    'scene_number': 2,
                    'batch_numbers': [1, 2],
                    'expected_batch_count': 1,
                    'expected_batch_numbers': [1],
                    'expeected_batch_sizes': [3],
                    'expected_batch_sizes': [25]
                },
                {
                    'command': 'MergeScenesMergeBatchesCommandTest',
                    'scene_numbers': [1, 2, 3],
                    'batch_numbers': [2, 3, 4],
                    'expected_scene_count': 2,
                    'expected_scene_numbers': [1, 2],
                    'expected_scene_sizes': [3, 1],
                    'expected_scene_linecounts': [61, 3],
                    'expected_scene_batches': [[1,2,3], [1]],
                    'expected_scene_batch_sizes': [[14, 41, 6], [3]]
                },
                {
                    'command': 'MergeSplitScenesCommandTest',
                    'scene_numbers': [1,2,3,4],
                    'expected_merge_scene_count': 1,
                    'expected_merge_scene_linecount': 64,
                    'expected_merge_scene_batches': [1, 2, 3, 4, 5, 6],
                    'split_scene_batch_number': 4,
                    'expected_split_scene_count': 2,
                    'expected_split_scene_batches': [[1, 2, 3], [1, 2, 3]],
                    'expected_split_scene_linecount': [42, 22],
                    'expected_split_first_lines': [
                        (1,"いつものように食事が終わるまでは誰も入れないでくれ.", "As usual, don't let anyone in until the meal is over."),
                        (43, "いくらで雇われた.", "How much were you hired for?")
                        ]
                }
            ]
        }
    ]

    def test_Commands(self):
        for test_case in self.command_test_cases:
            data = test_case['data']
            log_test_name(f"Testing commands on {data.get('movie_name')}")

            datamodel : ProjectDataModel = CreateTestDataModel(data, self.options)
            file : SubtitleFile = datamodel.project.subtitles

            with self.subTest("BatchSubtitlesCommand"):
                self.BatchSubtitlesCommandTests(file, datamodel, test_case.get('BatchSubtitlesCommand'))

            AddTranslations(file, data, 'translated')

            for command_data in test_case['tests']:
                command = command_data['command']

                with self.subTest(command):
                    log_test_name(f"{command} test")
                    if command == 'MergeSceneCommandTest':
                        self.MergeSceneCommandTest(file, datamodel, command_data)
                    elif command == 'MergeBatchesCommandTest':
                        self.MergeBatchesCommandTest(file, datamodel, command_data)
                    elif command == 'MergeScenesMergeBatchesCommandTest':
                        self.MergeScenesMergeBatchesCommandTest(file, datamodel, command_data)
                    elif command == 'MergeSplitScenesCommandTest':
                        self.MergeSplitScenesCommandTest(file, datamodel, command_data)

    def BatchSubtitlesCommandTests(self, file : SubtitleFile, datamodel : ProjectDataModel, test_data : dict):
        expected_scene_count = test_data['expected_scene_count']
        expected_scene_sizes = test_data['expected_scene_sizes']
        expected_scene_linecounts = test_data['expected_scene_linecounts']

        batch_command = BatchSubtitlesCommand(datamodel.project, datamodel.project_options)
        self.assertTrue(batch_command.execute())
        self.assertTrue(len(file.scenes) > 0)

        log_input_expected_result("Scene count", expected_scene_count, len(file.scenes))
        self.assertEqual(len(file.scenes), 4)

        for i in range(len(file.scenes)):
            log_input_expected_result("Scene size", expected_scene_sizes[i], file.scenes[i].size)
            log_input_expected_result("Scene line count", expected_scene_linecounts[i], file.scenes[i].linecount)
            self.assertEqual(file.scenes[i].size, expected_scene_sizes[i])
            self.assertEqual(file.scenes[i].linecount, expected_scene_linecounts[i])

    def MergeSceneCommandTest(self, file : SubtitleFile, datamodel : ProjectDataModel, test_data : dict):
        merge_scene_numbers = test_data['scene_numbers']

        undo_expected_scene_count = len(file.scenes)
        undo_expected_scene_numbers = [scene.number for scene in file.scenes]
        undo_expected_scene_sizes = [scene.size for scene in file.scenes]
        undo_expected_scene_linecounts = [scene.linecount for scene in file.scenes]
        undo_expected_scene_batches = [[batch.number for batch in scene.batches] for scene in file.scenes]

        merge_scenes_command = MergeScenesCommand(merge_scene_numbers, datamodel)
        self.assertTrue(merge_scenes_command.execute())

        expected_scene_count = test_data['expected_scene_count']
        expected_merged_scene_numbers = test_data['expected_merged_scene_numbers']
        expected_merged_linecounts = test_data['expected_merged_linecounts']
        expected_merged_scene_batches = test_data['expected_merged_scene_batches']

        merge_result_scene_numbers = [scene.number for scene in file.scenes]
        log_input_expected_result("Merged scenes", (expected_scene_count, expected_merged_scene_numbers), (len(file.scenes), merge_result_scene_numbers))
        self.assertEqual(len(file.scenes), expected_scene_count)
        self.assertSequenceEqual(merge_result_scene_numbers, expected_merged_scene_numbers)
        self.assertSequenceEqual([scene.linecount for scene in file.scenes], expected_merged_linecounts)

        merged_scene = file.GetScene(merge_scene_numbers[0])

        merged_scene_batch_numbers = [batch.number for batch in merged_scene.batches]
        log_input_expected_result("Merged scene batches", expected_merged_scene_batches, merged_scene_batch_numbers)
        self.assertSequenceEqual(merged_scene_batch_numbers, expected_merged_scene_batches)

        self.assertTrue(merge_scenes_command.can_undo)
        self.assertTrue(merge_scenes_command.undo())

        undo_merge_result_scene_numbers = [scene.number for scene in file.scenes]
        log_input_expected_result("Scenes after undo", (undo_expected_scene_count, undo_expected_scene_numbers), (len(file.scenes), undo_merge_result_scene_numbers))

        self.assertEqual(len(file.scenes), undo_expected_scene_count)
        self.assertSequenceEqual(undo_merge_result_scene_numbers, undo_expected_scene_numbers)
        self.assertSequenceEqual([scene.size for scene in file.scenes], undo_expected_scene_sizes)
        self.assertSequenceEqual([scene.linecount for scene in file.scenes], undo_expected_scene_linecounts)
        self.assertSequenceEqual([[batch.number for batch in scene.batches] for scene in file.scenes], undo_expected_scene_batches)

    def MergeBatchesCommandTest(self, file : SubtitleFile, datamodel : ProjectDataModel, test_data : dict):
        scene_number = test_data['scene_number']
        batch_numbers = test_data['batch_numbers']

        merge_scene = file.GetScene(scene_number)
        undo_expected_batch_count = merge_scene.size
        undo_expected_batch_numbers = [batch.number for batch in merge_scene.batches]
        undo_expected_batch_sizes = [batch.size for batch in merge_scene.batches]

        merge_batches_command = MergeBatchesCommand(scene_number, batch_numbers, datamodel)
        self.assertTrue(merge_batches_command.execute())

        expected_batch_count = test_data['expected_batch_count']
        expected_batch_numbers = test_data['expected_batch_numbers']
        expected_batch_sizes = test_data['expected_batch_sizes']

        merged_scene_batch_numbers = [batch.number for batch in merge_scene.batches]

        log_input_expected_result("Merged scene batches", (expected_batch_count, expected_batch_numbers), (len(merge_scene.batches), merged_scene_batch_numbers))
        self.assertEqual(len(merge_scene.batches), expected_batch_count)
        self.assertSequenceEqual(merged_scene_batch_numbers, expected_batch_numbers)
        self.assertSequenceEqual([batch.size for batch in merge_scene.batches], expected_batch_sizes)

        self.assertTrue(merge_batches_command.can_undo)
        self.assertTrue(merge_batches_command.undo())

        log_input_expected_result("Batches after undo", (undo_expected_batch_count, undo_expected_batch_numbers), (len(merge_scene.batches), [batch.number for batch in merge_scene.batches]))
        self.assertEqual(len(merge_scene.batches), undo_expected_batch_count)
        self.assertSequenceEqual([batch.number for batch in merge_scene.batches], undo_expected_batch_numbers)
        self.assertSequenceEqual([batch.size for batch in merge_scene.batches], undo_expected_batch_sizes)

    def MergeScenesMergeBatchesCommandTest(self, file : SubtitleFile, datamodel : ProjectDataModel, test_data : dict):
        # Merge scenes, then merge batches in the merged scenes, then undo both
        merge_scene_numbers = test_data['scene_numbers']
        merge_batch_numbers = test_data['batch_numbers']

        undo_expected_scene_count = len(file.scenes)
        undo_expected_scene_numbers = [scene.number for scene in file.scenes]
        undo_expected_scene_sizes = [scene.size for scene in file.scenes]
        undo_expected_scene_linecounts = [scene.linecount for scene in file.scenes]
        undo_expected_scene_batches = [[batch.number for batch in scene.batches] for scene in file.scenes]
        undo_expected_scene_batch_sizes = [[batch.size for batch in scene.batches] for scene in file.scenes]

        merge_scenes_command = MergeScenesCommand(merge_scene_numbers, datamodel)
        self.assertTrue(merge_scenes_command.execute())

        merge_batches_command = MergeBatchesCommand(merge_scene_numbers[0], merge_batch_numbers, datamodel)
        self.assertTrue(merge_batches_command.execute())

        expected_scene_count = test_data['expected_scene_count']
        expected_scene_numbers = test_data['expected_scene_numbers']
        expected_scene_sizes = test_data['expected_scene_sizes']
        expected_scene_linecounts = test_data['expected_scene_linecounts']
        expected_scene_batches = test_data['expected_scene_batches']
        expected_scene_batch_sizes = test_data['expected_scene_batch_sizes']

        log_input_expected_result("Merged scenes", (expected_scene_count, expected_scene_numbers), (len(file.scenes), [scene.number for scene in file.scenes]))
        self.assertEqual(len(file.scenes), expected_scene_count)
        self.assertSequenceEqual([scene.number for scene in file.scenes], expected_scene_numbers)
        self.assertSequenceEqual([scene.size for scene in file.scenes], expected_scene_sizes)
        self.assertSequenceEqual([scene.linecount for scene in file.scenes], expected_scene_linecounts)

        scene_batches = [[batch.number for batch in scene.batches] for scene in file.scenes]
        log_input_expected_result("Merged scene batches", expected_scene_batches, scene_batches)
        self.assertSequenceEqual(scene_batches, expected_scene_batches)
        scene_batch_sizes = [[batch.size for batch in scene.batches] for scene in file.scenes]
        log_input_expected_result("Merged scene batch sizes", expected_scene_batch_sizes, scene_batch_sizes)
        self.assertSequenceEqual(scene_batch_sizes, expected_scene_batch_sizes)

        self.assertTrue(merge_batches_command.can_undo)
        self.assertTrue(merge_batches_command.undo())

        self.assertTrue(merge_scenes_command.can_undo)
        self.assertTrue(merge_scenes_command.undo())

        undo_merge_result_scene_numbers = [scene.number for scene in file.scenes]
        log_input_expected_result("Scenes after undo", (undo_expected_scene_count, undo_expected_scene_numbers), (len(file.scenes), undo_merge_result_scene_numbers))

        self.assertEqual(len(file.scenes), undo_expected_scene_count)
        self.assertSequenceEqual(undo_merge_result_scene_numbers, undo_expected_scene_numbers)
        self.assertSequenceEqual([scene.size for scene in file.scenes], undo_expected_scene_sizes)
        self.assertSequenceEqual([scene.linecount for scene in file.scenes], undo_expected_scene_linecounts)
        self.assertSequenceEqual([[batch.number for batch in scene.batches] for scene in file.scenes], undo_expected_scene_batches)
        self.assertSequenceEqual([[batch.size for batch in scene.batches] for scene in file.scenes], undo_expected_scene_batch_sizes)

    def MergeSplitScenesCommandTest(self, file : SubtitleFile, datamodel : ProjectDataModel, test_data : dict):
        # Merge scenes, then split the merged scene, then undo both
        merge_scene_numbers = test_data['scene_numbers']
        split_scene_batch_number = test_data['split_scene_batch_number']

        undo_merge_expected_scene_count = len(file.scenes)
        undo_merge_expected_scene_numbers = [scene.number for scene in file.scenes]
        undo_merge_expected_scene_linecount = [scene.linecount for scene in file.scenes]
        undo_merge_expected_scene_batches = [[batch.number for batch in scene.batches] for scene in file.scenes]

        # Merge scenes
        merge_scenes_command = MergeScenesCommand(merge_scene_numbers, datamodel)
        self.assertTrue(merge_scenes_command.execute())

        expected_merge_scene_count = test_data['expected_merge_scene_count']
        expected_merge_scene_batches = test_data['expected_merge_scene_batches']
        expected_merge_scene_linecount = test_data['expected_merge_scene_linecount']

        log_input_expected_result("Merged scenes", (expected_merge_scene_count, merge_scene_numbers), (len(file.scenes), [scene.number for scene in file.scenes]))
        self.assertEqual(len(file.scenes), expected_merge_scene_count)

        merged_scene = file.GetScene(merge_scene_numbers[0])
        merged_scene_batches = [batch.number for batch in merged_scene.batches]

        self.assertEqual(merged_scene.linecount, expected_merge_scene_linecount)

        log_input_expected_result("Merged scene batches", expected_merge_scene_batches, merged_scene_batches)
        self.assertSequenceEqual(merged_scene_batches, expected_merge_scene_batches)

        undo_split_expected_scene_count = len(file.scenes)
        undo_split_expected_scene_numbers = [scene.number for scene in file.scenes]
        undo_split_expected_scene_linecount = [scene.linecount for scene in file.scenes]
        undo_split_expected_scene_batches = [[(batch.number, batch.first_line_number) for batch in scene.batches] for scene in file.scenes]

        # Split the scene
        split_scenes_command = SplitSceneCommand(merge_scene_numbers[0], split_scene_batch_number, datamodel)
        self.assertTrue(split_scenes_command.execute())

        expected_split_scene_count = test_data['expected_split_scene_count']
        expected_split_scene_batches = test_data['expected_split_scene_batches']
        expected_split_scene_linecount = test_data['expected_split_scene_linecount']
        expected_split_first_lines = test_data['expected_split_first_lines']

        log_input_expected_result("Split scenes", (expected_split_scene_count, [merge_scene_numbers[0]]), (len(file.scenes), [scene.number for scene in file.scenes]))
        self.assertEqual(len(file.scenes), expected_split_scene_count)
        self.assertEqual([scene.linecount for scene in file.scenes], expected_split_scene_linecount)

        split_scenes_batches = [[batch.number for batch in scene.batches] for scene in file.scenes]
        log_input_expected_result("Split scene batches", expected_split_scene_batches, split_scenes_batches)
        self.assertSequenceEqual(split_scenes_batches, expected_split_scene_batches)

        for i in range(len(expected_split_first_lines)):
            scene = file.scenes[i]
            first_original = scene.batches[0].originals[0].text
            first_translated = scene.batches[0].translated[0].text
            log_input_expected_result(f"Scene {scene.number} first line", expected_split_first_lines[i], (scene.first_line_number, first_original, first_translated))
            self.assertEqual(scene.first_line_number, expected_split_first_lines[i][0])
            self.assertEqual(first_original, expected_split_first_lines[i][1])
            self.assertEqual(first_translated, expected_split_first_lines[i][2])

        # Undo split scene
        self.assertTrue(split_scenes_command.can_undo)
        self.assertTrue(split_scenes_command.undo())

        log_input_expected_result("Scenes after undo split", (undo_merge_expected_scene_count, undo_merge_expected_scene_numbers), (len(file.scenes), [scene.number for scene in file.scenes]))
        self.assertEqual(len(file.scenes), undo_split_expected_scene_count)
        self.assertSequenceEqual([scene.number for scene in file.scenes], undo_split_expected_scene_numbers)
        self.assertSequenceEqual([scene.linecount for scene in file.scenes], undo_split_expected_scene_linecount)
        self.assertSequenceEqual([[(batch.number, batch.first_line_number) for batch in scene.batches] for scene in file.scenes], undo_split_expected_scene_batches)

        # Undo merge scene
        self.assertTrue(merge_scenes_command.can_undo)
        self.assertTrue(merge_scenes_command.undo())

        log_input_expected_result("Scenes after undo merge", (undo_merge_expected_scene_count, undo_merge_expected_scene_numbers), (len(file.scenes), [scene.number for scene in file.scenes]))
        self.assertEqual(len(file.scenes), undo_merge_expected_scene_count)
        self.assertSequenceEqual([scene.number for scene in file.scenes], undo_merge_expected_scene_numbers)
        self.assertSequenceEqual([scene.linecount for scene in file.scenes], undo_merge_expected_scene_linecount)
        self.assertSequenceEqual([[batch.number for batch in scene.batches] for scene in file.scenes], undo_merge_expected_scene_batches)



