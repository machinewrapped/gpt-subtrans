import unittest
from PySubtitle.Helpers.Tests import log_input_expected_result, log_test_name
from PySubtitle.Helpers.Text import BreakDialogOnOneLine, NormaliseDialogTags

class TestTextHelpers(unittest.TestCase):
    dialog_marker = "- "

    normalise_tags_cases = {
        "This is a test": "This is a test",
        "- This is a test": "This is a test",
        "- This is a test\n- I also think that": "- This is a test\n- I also think that",
        "This is a test\n- I also think that": "- This is a test\n- I also think that",
        "- This is a test\nI also think that": "- This is a test\n- I also think that",
        "- This is a test - a harder one\n- I hope it passes": "- This is a test - a harder one\n- I hope it passes",
        "- This is a test - a harder one\nI hope it passes": "- This is a test - a harder one\n- I hope it passes"
    }

    break_dialog_on_one_line_cases = {
        "This is a test": "This is a test",
        "This is a test... - This should be on another line": "This is a test...\n- This should be on another line",
        "This is a test - it shouldn't break this one": "This is a test - it shouldn't break this one",
        "- This is a test\n- I also think that": "- This is a test\n- I also think that",
        "This is a test! - A hard one! - I hope it passes": "This is a test!\n- A hard one!\n- I hope it passes",
        "- This is a test! - A hard one! - I hope it passes": "- This is a test!\n- A hard one!\n- I hope it passes",
    }

    def test_NormaliseDialogTags(self):
        log_test_name("NormaliseDialogTags")
        for text, expected in self.normalise_tags_cases.items():
            with self.subTest(text=text):
                result = NormaliseDialogTags(text, self.dialog_marker)
                log_input_expected_result(text, expected, result)
                self.assertEqual(result, expected)

    def test_BreakDialogOnOneLine(self):
        log_test_name("BreakDialogOnOneLine")
        for text, expected in self.break_dialog_on_one_line_cases.items():
            with self.subTest(text=text):
                result = BreakDialogOnOneLine(text, self.dialog_marker)
                log_input_expected_result(text, expected, result)
                self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()