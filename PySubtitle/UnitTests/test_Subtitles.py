import unittest
from PySubtitle.Helpers.Tests import log_input_expected_result, log_invalid_testcase, log_test_name
from PySubtitle.Helpers.Subtitles import MergeSubtitles, MergeTranslations
from PySubtitle.SubtitleLine import SubtitleLine


class TestSubtitles(unittest.TestCase):

    example_line_1 = SubtitleLine("1\n00:00:01,000 --> 00:00:02,000\nThis is line 1")
    example_line_2 = SubtitleLine("2\n00:00:02,500 --> 00:00:03,500\nThis is line 2")
    example_line_3 = SubtitleLine("3\n00:00:04,000 --> 00:00:06,200\nThis is line 3")
    example_line_4 = SubtitleLine("4\n00:00:06,500 --> 00:00:07,500\nThis is line 4")
    example_line_5 = SubtitleLine("5\n00:00:08,000 --> 00:00:09,000\nThis is line 5.\nThis is line 5 continued")
    example_line_11 = SubtitleLine("11\n00:00:10,000 --> 00:00:11,000\nThis is line 11, which is a bit longer!")
    alternative_line_1 = SubtitleLine("1\n00:00:01,000 --> 00:00:02,000\nThis is an alternative line 1")
    alternative_line_2 = SubtitleLine("2\n00:00:02,500 --> 00:00:03,500\nThis is an alternative line 2")

    merge_subtitles_cases = [
        (
            [ example_line_1, example_line_2 ],
            SubtitleLine("1\n00:00:01,000 --> 00:00:03,500\nThis is line 1\nThis is line 2")
        ),
        (
            [ example_line_1, example_line_2, example_line_3 ],
            SubtitleLine("1\n00:00:01,000 --> 00:00:06,200\nThis is line 1\nThis is line 2\nThis is line 3")
        ),
        (
            [ example_line_11 ],
            SubtitleLine("11\n00:00:10,000 --> 00:00:11,000\nThis is line 11, which is a bit longer!")
        ),
        (
            [ example_line_4, example_line_5 ],
            SubtitleLine("4\n00:00:06,500 --> 00:00:09,000\nThis is line 4\nThis is line 5.\nThis is line 5 continued")
        )
    ]

    def test_MergeSubtitles(self):
        log_test_name("MergeSubtitles")
        for source, expected in self.merge_subtitles_cases:
            with self.subTest(source=source):
                lines = [SubtitleLine(line) for line in source]
                expected_line = SubtitleLine(expected)
                result = MergeSubtitles(lines)
                log_input_expected_result(lines, expected_line, result)
                self.assertEqual(result, expected_line)

    merge_translation_cases = [
        (
            [ example_line_1, example_line_2 ],
            [ example_line_3, example_line_4 ],
            [ example_line_1, example_line_2, example_line_3, example_line_4 ]
        ),
        (
            [ example_line_1, example_line_2 ],
            [ example_line_1, example_line_3 ],
            [ example_line_1, example_line_2, example_line_3 ]
        ),
        (
            [ example_line_1, example_line_2 ],
            [ alternative_line_1, example_line_3 ],
            [ alternative_line_1, example_line_2, example_line_3 ]
        ),
        (
            [ example_line_1, example_line_2 ],
            [ alternative_line_1, alternative_line_2 ],
            [ alternative_line_1, alternative_line_2 ]
        )
    ]

    def test_MergeTranslations(self):
        log_test_name("MergeTranslations")
        for group_1, group_2, expected in self.merge_translation_cases:
            with self.subTest(group_1=group_1, group_2=group_2):
                merged_lines = MergeTranslations(group_1, group_2)
                log_input_expected_result(f"Merged {len(group_1)} lines and {len(group_2)} lines",
                                          expected,
                                          merged_lines)

                self.assertSequenceEqual(merged_lines, expected)

if __name__ == '__main__':
    unittest.main()