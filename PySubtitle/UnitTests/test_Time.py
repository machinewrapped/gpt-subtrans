import unittest
from datetime import timedelta
from PySubtitle.Helpers.Tests import log_input_expected_error, log_input_expected_result, log_test_name
from PySubtitle.Helpers.Time import GetTimeDelta

class TestTimeHelpers(unittest.TestCase):
    get_timedelta_cases = [
        (timedelta(hours=1, minutes=30, seconds=45), timedelta(hours=1, minutes=30, seconds=45)),
        ("01:30:45,000", timedelta(hours=1, minutes=30, seconds=45)),
        ("30:45,000", timedelta(hours=0, minutes=30, seconds=45)), # Without hours
        ("01:30:45", timedelta(hours=1, minutes=30, seconds=45, milliseconds=0)), # Without milliseconds
        ("30:45", timedelta(hours=0, minutes=30, seconds=45, milliseconds=0)), # Without hours and milliseconds
        ("45,250", timedelta(hours=0, minutes=0, seconds=45, milliseconds=250)), # Without hours and minutes
        ("01:30:45.123", timedelta(hours=1, minutes=30, seconds=45, milliseconds=123)),  # Non-standard milliseconds separator
        ("30:45.123", timedelta(hours=0, minutes=30, seconds=45, milliseconds=123)),  # Without hours, non-standard milliseconds separator
        ("01:30:45，123", timedelta(hours=1, minutes=30, seconds=45, milliseconds=123)),  # Full-width comma
        ("30:45．123", timedelta(hours=0, minutes=30, seconds=45, milliseconds=123)),  # Without hours, full-width period
        ("10:20:30,400,500", timedelta(hours=10, minutes=20, seconds=30, milliseconds=400)),
        ("100:20:30,400,500,600", timedelta(hours=100, minutes=20, seconds=30, milliseconds=400)),
        (None, None),
        ("invalid", ValueError),
    ]

    def test_GetTimeDelta(self):
        log_test_name("GetTimeDelta")
        for value, expected in self.get_timedelta_cases:
            with self.subTest(value=value):
                error_expected = (expected == ValueError)
                result = GetTimeDelta(value, raise_exception = not error_expected)
                if error_expected:
                    log_input_expected_error(value, expected, result)
                    self.assertIsInstance(result, ValueError)
                else:
                    log_input_expected_result(value, expected, result)
                    self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()