import pytest
from pathlib import Path
from backend.services.preprocess_source_code import preprocess_source_code

# Sample content for Java files
sample_java_content = """
public class SampleClass {
    public static void main(String[] args) {
        int newNumber = 0;
        System.out.println("Hello, World!");
    }
}
"""

@pytest.fixture
def create_sample_java_files(tmp_path):
    """
    Creates a temporary directory structure with .java files
    """
    # Create root directory for source code
    root_dir = tmp_path / "source_code"
    root_dir.mkdir()

    # Create sample .java files
    java_file_1 = root_dir / "SampleClass1.java"
    java_file_1.write_text(sample_java_content)

    java_file_2 = root_dir / "SampleClass2.java"
    java_file_2.write_text(sample_java_content)

    return root_dir

def test_preprocess_source_code(create_sample_java_files):
    # Directory setup and execution
    root_dir = create_sample_java_files
    result = preprocess_source_code(root_dir)

    # Validate results
    assert len(result) == 2, "Expected 2 .java files to be processed"
    
    # Check if results match expected preprocessing (i.e., tokens without stop words)
    expected_content = "sample class main string args number system out println hello world"
    for _, file_name, content in result:
        assert content == expected_content, f"Unexpected content for {file_name}"

def test_empty_directory(tmp_path):
    # Test with an empty directory
    empty_dir = tmp_path / "empty_source_code"
    empty_dir.mkdir()
    
    result = preprocess_source_code(empty_dir)
    assert result == [], "Expected no files to be processed in an empty directory"
