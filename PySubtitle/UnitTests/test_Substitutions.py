import unittest
from PySubtitle.Helpers.Substitutions import ParseSubstitutions, PerformSubstitutions, PerformSubstitutions2
from PySubtitle.Helpers.Tests import log_test_name, log_input_expected_result

class TestSubstitutions(unittest.TestCase):
    parse_cases = [
        ([], {}),
        ("", {}),
        ({"before": "after", "hello": "world"}, {"before": "after", "hello": "world"}),
        ("before::after\nhello::world", {"before": "after", "hello": "world"}),
        (["before::after", "hello::world"], {"before": "after", "hello": "world"}),
    ]

    def test_ParseSubstitutions(self):
        log_test_name("ParseSubstitutions")
        for value, expected in self.parse_cases:
            with self.subTest(value=value):
                result = ParseSubstitutions(value)
                log_input_expected_result(value, expected, result)
                self.assertEqual(result, expected)

    perform_cases = [
        (["before::after", "hello::world"], "before hello", "after world", False),
        ({"before": "after", "hello": "world"}, "This is the string before", "This is the string after", False),
        ({"bef": "aft", "hello": "world"}, "before hello", "before world", False),
        ({"李王": "Li Wang"}, "Mr. 李王 is a Chinese name", "Mr. Li Wang is a Chinese name", False),
        ({"東京": "Tokyo"}, "東京 is the capital of Japan", "Tokyo is the capital of Japan", False),
        ({"big": "small"}, "The big brown fox jumped over the big fence", "The small brown fox jumped over the small fence", False),
        ({"東京": "Tokyo"}, "東京都は日本の首都です", "Tokyo都は日本の首都です", True),
        ({"李王": "Li Wang"}, "在学术交流会上，李王详细阐述了他的观点。晚宴上，大家继续讨论李王的提议。", "在学术交流会上，Li Wang详细阐述了他的观点。晚宴上，大家继续讨论Li Wang的提议。", True),
    ]

    def test_PerformSubstitutions(self):
        log_test_name("PerformSubstitutions")
        for substitutions, value, expected, match_partial in self.perform_cases:
            with self.subTest(value=value):
                substitutions = ParseSubstitutions(substitutions)
                result = PerformSubstitutions(substitutions, value, match_partial)
                log_input_expected_result((value, substitutions), expected, result)
                self.assertEqual(result, expected)

    def test_PerformSubstitutions2(self):
        log_test_name("PerformSubstitutions2")
        for substitutions, value, expected, _ in self.perform_cases:
            with self.subTest(value=value):
                substitutions = ParseSubstitutions(substitutions)
                result = PerformSubstitutions2(substitutions, value)
                log_input_expected_result((value, substitutions), expected, result)
                self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()