import unittest
from backend.services.preprocess import Preprocessor

class test_preprocess(unittest.TestCase):
    def test_wrong_path(self):
        text = "uhhh lets preProcess some texts!!"
        stop_words_path = "/stop_words/java-keywords-bugs.txt"

        expected_result = ""
        actual_result = Preprocessor.preprocess_text(text, stop_words_path)

        self.assertEqual(expected_result, actual_result)

    