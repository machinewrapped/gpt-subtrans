import unittest
import regex
from datetime import timedelta

from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.Helpers.Tests import log_input_expected_result, log_test_name
from PySubtitle.Helpers.Subtitles import MergeSubtitles, MergeTranslations, FindSplitPoint, GetProportionalDuration
from PySubtitle.SubtitleProcessor import SubtitleProcessor

class TestSubtitles(unittest.TestCase):

    example_line_1 = SubtitleLine("1\n00:00:01,000 --> 00:00:02,000\nThis is line 1")
    example_line_2 = SubtitleLine("2\n00:00:02,500 --> 00:00:03,500\nThis is line 2")
    example_line_3 = SubtitleLine("3\n00:00:04,000 --> 00:00:06,200\nThis is line 3")
    example_line_4 = SubtitleLine("4\n00:00:06,500 --> 00:00:07,500\nThis is line 4")
    example_line_5 = SubtitleLine("5\n00:00:08,000 --> 00:00:09,500\nThis is line 5.\nThis is line 5 continued")
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
            SubtitleLine("4\n00:00:06,500 --> 00:00:09,500\nThis is line 4\nThis is line 5.\nThis is line 5 continued")
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

    split_point_cases = [
        ("1\n00:00:01,000 --> 00:00:05,000\nThis is a test subtitle, break after comma.", "This is a test subtitle,"),
        ("2\n00:00:06,000 --> 00:00:10,000\nSecond test subtitle. Break after period.", "Second test subtitle."),
        ("3\n00:00:11,000 --> 00:00:15,000\nThird test subtitle! Break after exclamation mark.", "Third test subtitle!"),
        ("4\n00:00:16,000 --> 00:00:20,000\nFourth test subtitle? Break after question mark.", "Fourth test subtitle?"),
        ("5\n00:00:21,000 --> 00:00:25,000\nFifth test subtitle... Break after ellipsis.", "Fifth test subtitle..."),
        ("6\n00:00:26,000 --> 00:00:30,000\nSixth test subtitle.\nBreak after newline.", "Sixth test subtitle."),
        ("7\n00:00:31,000 --> 00:00:35,000\nSeventh test subtitle.\nBreak after newline, not after the comma even if it is closer to the middle of the line.", "Seventh test subtitle."),
        ("8\n00:00:36,000 --> 00:00:40,000\nEighth test subtitle, break after second comma, because it is closer to the middle.", "Eighth test subtitle, break after second comma,"),
        ("9\n00:00:36,000 --> 00:00:40,000\nNinth test subtitle. Break after the period, not the comma even if it is closer to the middle.", "Ninth test subtitle."),
        ("10\n00:00:41,000 --> 00:00:45,000\nTenth test subtitle, <i>We should not split here, even though there is a comma in the italic block.</i>", "Tenth test subtitle,"),
        ("11\n00:00:46,000 --> 00:00:50,000\nEleventh test subtitle！Break after full-width exclamation mark.", "Eleventh test subtitle！"),
        ("12\n00:00:51,000 --> 00:00:55,000\nTwelfth test subtitle.    Break after three spaces.", "Twelfth test subtitle."),
        ("13\n00:00:56,000 --> 00:01:00,000\n\"Is this the 13th subtitle?\" Break after the quote.", "\"Is this the 13th subtitle?\""),
        ("15\n00:01:06,000 --> 00:01:10,000\nThey say, \"We should not! Split a quotation!\"", "They say,"),
        ("16\n00:01:11,000 --> 00:01:15,000\nWe can split <i>a block in tags, if they do not match</b>", "We can split <i>a block in tags,"),
    ]

    def test_FindSplitPoint(self):
        log_test_name("FindSplitPoint")
        split_sequences = [
            r"\n",  # Newline has the highest priority
            r"(?=\([^)]*\)|\[[^\]]*\])",  # Look ahead to find a complete parenthetical or bracketed block to split before
            r"(?=\"[^\"]*\")",  # Look ahead to find a complete block within double quotation marks
            r"(?=<([ib])>[^<]*</\1>)",  # Look ahead to find a block in italics or bold
            r"[.!?](\s|\")",  # End of sentence punctuation like '!', '?', possibly at the end of a quote
            r"[？！。…]", # Full-width punctuation (does not need to be followed by whitespace)
            r"[,，、﹑](\s|\")?",  # Various forms of commas
            r" {3,}"  # Three or more spaces
        ]

        split_patterns = [regex.compile(sequence) for sequence in split_sequences]

        min_duration = timedelta(seconds=1)
        min_split_chars = 3

        for source, first_part in self.split_point_cases:
            with self.subTest(source=source):
                line = SubtitleLine(source)
                break_point = FindSplitPoint(line, split_patterns, min_duration, min_split_chars)
                result = line.text[:break_point].strip()
                log_input_expected_result(line, first_part, result)
                self.assertEqual(result, first_part)

    proportional_duration_cases = [
        (example_line_1, 6, timedelta(seconds=0.5), timedelta(seconds=0.5)),
        (example_line_2, 4, timedelta(seconds=0.8), timedelta(seconds=0.8)),
        (example_line_3, 10, timedelta(seconds=0.75), timedelta(seconds=1.0, microseconds=571429)),
        (example_line_3, 14, timedelta(seconds=0.75), timedelta(seconds=2.0, microseconds=200000)),
        (example_line_5, 8, timedelta(seconds=0.6), timedelta(seconds=0.6)),
        (example_line_5, 25, timedelta(seconds=0.6), timedelta(microseconds=937500))
    ]

    def test_GetProportionalDuration(self):
        log_test_name("GetProportionalDuration")
        for line, characters, min_duration, expected_duration in self.proportional_duration_cases:
            with self.subTest(line=line, characters=characters):
                result = GetProportionalDuration(line, characters, min_duration=min_duration)
                log_input_expected_result((line.text, characters, min_duration.total_seconds()), expected_duration, result)
                self.assertEqual(result, expected_duration)

class SubtitleProcessorTests(unittest.TestCase):
    example_line_1 = SubtitleLine("1\n00:00:01,000 --> 00:00:02,000\nThis is line 1")
    example_line_2 = SubtitleLine("2\n00:00:02,500 --> 00:00:03,500\nThis is line 2")

    preprocess_cases = [
        ([example_line_1, example_line_2], {}, [example_line_1, example_line_2]),  # No changes
    ]

    def test_Preprocess(self):
        log_test_name("PreprocessSubtitles")
        for source, settings, expected in self.preprocess_cases:
            with self.subTest(source=source, settings=settings):
                processor = SubtitleProcessor(settings)
                result = processor.PreprocessSubtitles(source, settings)
                self.assertSequenceEqual(result, expected)

    postprocess_cases = [
        ([example_line_1, example_line_2], {}, [example_line_1, example_line_2]),  # No changes
    ]

    def test_Postprocess(self):
        log_test_name("PostprocessSubtitles")
        for source, settings, expected in self.postprocess_cases:
            with self.subTest(source=source, settings=settings):
                processor = SubtitleProcessor(settings)
                result = processor.PostprocessSubtitles(source, settings)
                self.assertSequenceEqual(result, expected)

if __name__ == '__main__':
    unittest.main()