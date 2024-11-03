import unittest
from backend.services.preprocess import Preprocessor

class test_preprocess(unittest.TestCase):
    def test_wrong_path(self):
        text = "uhhh lets preProcess some texts!!"
        stop_words_path = "stop_words/java-keywords-bugs.txt"

        expected_result = ""
        actual_result = Preprocessor.preprocess_text(text, stop_words_path)

        self.assertEqual(expected_result, actual_result)
    
    def test_bug_report_preprocessing(self):
        self.maxDiff = None

        bug_report_path = "temp_testing/bug_report_10.txt"
        
        expected_result = ""
        actual_result = preprocess_bug_report(bug_report_path)

        self.assertEqual(expected_result, actual_result)

    def test_pos_tagger(self):
        text = "files"

        expected_result = ""
        actual_result = Preprocessor.get_pos_tag(text)

        self.assertEqual(expected_result, actual_result)

    def test_lemmatize(self):
        text = "files"

        expected_result = ""
        actual_result = Preprocessor.lematize_tokens([text])

        print(Preprocessor.get_pos_tag(text))
        self.assertEqual(expected_result, actual_result)
