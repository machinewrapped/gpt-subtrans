import unittest
from PySubtitle.Helpers.Parse import ParseDelayFromHeader, ParseNames
from PySubtitle.Helpers.Tests import log_input_expected_result, log_test_name

class TestParseDelayFromHeader(unittest.TestCase):
    test_cases = [
        ("5", 5.0),
        ("10s", 10.0),
        ("5m", 300.0),
        ("500ms", 1.0),
        ("1500ms", 1.5),
        ("abc", 32.1),
        ("12x", 6.66),
    ]

    def test_ParseDelayFromHeader(self):
        log_test_name("ParseDelayFromHeader")
        for value, expected in self.test_cases:
            with self.subTest(value=value):
                result = ParseDelayFromHeader(value)
                log_input_expected_result(value, expected, result)
                self.assertEqual(result, expected)


class TestParseNames(unittest.TestCase):
    test_cases = [
        ("John, Jane, Alice", ["John", "Jane", "Alice"]),
        (["John", "Jane", "Alice"], ["John", "Jane", "Alice"]),
        ("Mike, Murray, Mabel, Marge", ["Mike", "Murray", "Mabel", "Marge"]),
        ("", []),
        ([] , []),
        ([""], [])
    ]

    def test_ParseNames(self):
        log_test_name("ParseNames")
        for value, expected in self.test_cases:
            with self.subTest(value=value):
                result = ParseNames(value)
                log_input_expected_result(value, expected, result)
                self.assertSequenceEqual(result, expected)

if __name__ == '__main__':
    unittest.main()