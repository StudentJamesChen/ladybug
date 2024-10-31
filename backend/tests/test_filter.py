"""
Tests to implement:

1. dir with only java files
2. dir with mixed file types
3. nested dirs with mixed file types
4. dir with empty subdirs
5. dir with subdirs containing only non-java files
6. large dir with multiple java files
7. hidden files and dirs
8. single java file
9. invalid path
10. empty repo
"""
from ..filter import filter_files
import pytest
from pathlib import Path

def test_filter_empty_repo(tmp_path):
    # Call filter on an empty directory (simulating an empty repo)
    result = filter_files(tmp_path)

    assert result == []

def test_filter_invalid_path(tmp_path):
    # Call filter on a non-existent path
    invalid_path = tmp_path / "nonexistent_repo"
    assert not invalid_path.exists()

    with pytest.raises(ValueError, match="is not a valid directory."):
        filter_files(invalid_path)

def test_filter_single_java_file(tmp_path):
    # Simulate a single java file passed into filter_files()
    java_file = tmp_path / "SingleFile.java"
    java_file.write_text("public class SingleFile {}")

    with pytest.raises(ValueError, match="is not a valid directory"):
        filter_files(java_file)

def test_filter_hidden_files(tmp_path):
    # Create a regular Java file
    java_file = tmp_path / "Regular.java"
    java_file.write_text("public class Regular {}")
    
    # Create a hidden Java file
    hidden_java_file = tmp_path / ".HiddenFile.java"
    hidden_java_file.write_text("public class HiddenFile {}")
    
    # Create a hidden non-Java file
    hidden_non_java_file = tmp_path / ".HiddenFile.txt"
    hidden_non_java_file.write_text("This is a text file.")

    result = filter_files(tmp_path)
    
    # Ensure only the visible Java file is included in the results
    assert Path(java_file) in result
    assert Path(hidden_java_file) not in result
    assert Path(hidden_non_java_file) not in result
    
    # Check that no hidden files remain in the input directory
    hidden_files = [f for f in tmp_path.rglob('*') if f.name.startswith('.')]
    assert len(hidden_files) == 0, "Hidden files remain in the directory"