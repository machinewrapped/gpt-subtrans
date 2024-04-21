import unittest
from PySubtitle.Helpers.Tests import log_input_expected_result
from PySubtitle.Helpers.Text import NormaliseDialogTags

class TestTextHelpers(unittest.TestCase):
    dialog_marker = "- "

    test_normalise_tags = {
        "This is a test": "This is a test",
        "- This is a test": "This is a test",
        "- This is a test\n- I also think that": "- This is a test\n- I also think that",
        "This is a test\n- I also think that": "- This is a test\n- I also think that",
        "- This is a test\nI also think that": "- This is a test\n- I also think that",
        "- This is a test - a harder one\n- I hope it passes": "- This is a test - a harder one\n- I hope it passes",
        "- This is a test - a harder one\nI hope it passes": "- This is a test - a harder one\n- I hope it passes"
    }

    def test_NormaliseDialogTags(self):
        for text, expected in self.test_normalise_tags.items():
            with self.subTest(text=text):
                result = NormaliseDialogTags(text, self.dialog_marker)
                log_input_expected_result(text, expected, result)
                self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()