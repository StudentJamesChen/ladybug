import unittest
from preprocess import Preprocessor
from preprocess_bug_report import preprocess_bug_report

class test_preprocess(unittest.TestCase):
    def test_wrong_path(self):
        text = "uhhh lets preProcess some texts!!"
        stop_words_path = "stop_words/java-keywords-bugs.txt"

        expected_result = ""
        actual_result = Preprocessor.preprocess_text(text, stop_words_path)

        self.assertEqual(expected_result, actual_result)
    
    def test_bug_report_preprocessing(self):
        bug_report_path = "temp_testing/bug_report_10.txt"
        
        expected_result = ""
        actual_result = preprocess_bug_report(bug_report_path)

        self.assertEqual(expected_result, actual_result)