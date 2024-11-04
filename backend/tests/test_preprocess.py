from ..preprocess import Preprocessor
import pytest

def test_camel_case_split():
    str1 = "camelCase"
    result = Preprocessor.camel_case_split(str1)

    assert result == ["camel", "Case"]
    return

def test_camel_case_split_long():
    str1 = "somewhatLongButNotHorriblyLongCamelCaseString"
    result = Preprocessor.camel_case_split(str1)

    assert result == ["somewhat", "Long", "But", "Not", "Horribly", "Long", "Camel",
                      "Case", "String"]
    
def test_camel_case_split_acronyms():
    str1 = "HTTPServerResponse"
    result = Preprocessor.camel_case_split(str1)

    assert result == ["HTTP", "Server", "Response"]

def test_camel_case_split_numbers():
    str1 = "Load2Files"
    result = Preprocessor.camel_case_split(str1)

    assert result == ["HTTP", "Server", "Response"]
