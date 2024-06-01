from copy import deepcopy

from GUI.Commands.MergeLinesCommand import MergeLinesCommand
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Helpers.TestCases import CreateTestDataModelBatched, SubtitleTestCase
from PySubtitle.Helpers.Tests import log_info, log_input_expected_result, log_test_name
from PySubtitle.Options import Options
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.UnitTests.TestData.chinese_dinner import chinese_dinner_data

class MergeLinesCommandTest(SubtitleTestCase):
    merge_lines_test_cases = [
        {
            'batch_number': (1,1),
            'lines_to_merge': [1,2,3],
            'expected_batch_size': 12,
            'expected_content': [
                {
                    'line': 1,
                    'original': "いつものように食事が終わるまでは誰も入れないでくれ.\nいつものやつを頼む星野だ 親父を頼む星野です.\n万事うまくいってます.",
                    'translated' : "As usual, don't let anyone in until the meal is over.\nIt's Hoshino, ordering the usual. Hoshino, asking for the boss.\nEverything is going smoothly.",
                    'start': '00:02:12,250',
                    'end': '00:03:31,040'
                }
            ]
        }

    ]

    def test_MergeLinesCommand(self):
        log_test_name("MergeLinesCommand")

        data = deepcopy(chinese_dinner_data)

        datamodel : ProjectDataModel = CreateTestDataModelBatched(data, options=self.options)
        subtitles: SubtitleFile = datamodel.project.subtitles

        undo_stack = []

        for test_case in self.merge_lines_test_cases:
            scene_number, batch_number = test_case['batch_number']
            lines_to_merge = test_case['lines_to_merge']
            expected_batch_size = test_case['expected_batch_size']
            expected_content = test_case['expected_content']

            batch = subtitles.GetBatch(scene_number, batch_number)
            log_info("Merging lines {lines_to_merge} in batch ({scene_number},{batch_number})")

            self.assertTrue(all([any([line.number == line_number for line in batch.originals]) for line_number in lines_to_merge]))

            command = MergeLinesCommand(lines_to_merge, datamodel=datamodel)
            undo_stack.append(command)
            self.assertTrue(command.execute())

            for line_data in expected_content:
                line_number = line_data['line']
                line = batch.GetOriginalLine(line_number)
                translated_line = batch.GetTranslatedLine(line_number)

                log_input_expected_result(f"Line {line_number}", (line.srt_start, line.srt_end), (line_data['start'], line_data['end']))
                log_input_expected_result("Batch size", len(batch.originals), expected_batch_size)
                log_input_expected_result("Original", line.text, line_data['original'])
                log_input_expected_result("Translated", line.translation, line_data['translated'])

                self.assertEqual(len(batch.originals), expected_batch_size)
                self.assertEqual(line.srt_start, line_data['start'])
                self.assertEqual(line.srt_end, line_data['end'])
                self.assertEqual(line.text, line_data['original'])
                self.assertEqual(line.translation, line_data['translated'])

                if translated_line:
                    self.assertEqual(translated_line.srt_start, line_data['start'])
                    self.assertEqual(translated_line.srt_end, line_data['end'])
                    self.assertEqual(translated_line.text, line_data['translated'])

        # Verify that undoing the command stack restores the original state
        for command in reversed(undo_stack):
            self.assertTrue(command.can_undo)
            self.assertTrue(command.undo())

        reference_datamodel : ProjectDataModel = CreateTestDataModelBatched(data, options=self.options)

        self._assert_same_as_reference(subtitles, reference_datamodel.project.subtitles)


