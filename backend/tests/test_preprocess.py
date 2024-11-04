import pytest
from backend.services.preprocess import Preprocessor
from nltk.corpus import wordnet as wn

# Sample data for testing
sample_text = "This is a sampleTextWithCamelCase and punctuation! And numbers: 12345."
stop_words_path = "stop_words.txt"

# Writing the stop words file for testing
@pytest.fixture(scope="module")
def stop_words_file(tmp_path_factory):
    stop_words_file = tmp_path_factory.mktemp("data") / "stop_words.txt"
    with open(stop_words_file, "w") as f:
        f.write("is\nand\na\nwith\n")
    return stop_words_file


def test_camel_case_split():
    # Test camel case splitting
    assert Preprocessor.camel_case_split("camelCaseWord") == ["camel", "Case", "Word"]
    assert Preprocessor.camel_case_split("HTMLParser") == ["HTML", "Parser"]
    assert Preprocessor.camel_case_split("simple") == ["simple"]


def test_tokenize_text():
    # Test tokenization with camel case splitting
    tokens = Preprocessor.tokenize_text("A quickSample for tokenizing CamelCaseWords.")
    assert tokens == ["A", "quick", "Sample", "for", "tokenizing", "Camel", "Case", "Words", "."]

    # Edge case: check empty string
    assert Preprocessor.tokenize_text("") == []


def test_remove_special_characters():
    # Test special characters and numbers removal
    result = Preprocessor.remove_special_characters("Hello, World! 123.")
    assert result == "Hello  World   "

    # Edge case: empty string
    assert Preprocessor.remove_special_characters("") == ""

    # Edge case: string with only special characters
    assert Preprocessor.remove_special_characters("!@#$%^&*()") == " "


def test_get_pos_tag():
    # Test POS tag mapping
    # assert Preprocessor.get_pos_tag("beautiful") == wn.ADJ
    assert Preprocessor.get_pos_tag("run") == wn.VERB
    assert Preprocessor.get_pos_tag("quickly") == wn.ADV
    assert Preprocessor.get_pos_tag("dog") == wn.NOUN

    # Edge case: unknown or rare word
    assert Preprocessor.get_pos_tag("xyzzy") == wn.NOUN  # Defaults to NOUN


def test_lematize_tokens():
    # Test lemmatization
    tokens = ["running", "dogs", "beautifully", "was"]
    lemmatized = Preprocessor.lematize_tokens(tokens)
    assert lemmatized == ["run", "dog", "beautifully", "be"]


def test_preprocess_text(stop_words_file):
    # Test preprocessing with stop words filtering, special character removal, tokenization, and lemmatization
    text = "This is a simpleText with Numbers123 and some StopWords!"
    result = Preprocessor.preprocess_text(text, stop_words_file)
    expected = "simple text number stop word"  # Expected output based on transformations
    assert result == expected

    # Edge case: empty string input
    assert Preprocessor.preprocess_text("", stop_words_file) == ""

    # Edge case: stop words file not found
    with pytest.raises(FileNotFoundError):
        Preprocessor.preprocess_text("Text with no stopwords file", "invalid_path.txt")
