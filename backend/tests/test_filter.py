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

def test_filter_empty_repo(tmp_path):
    # Call filter on an empty directory (simulating an empty repo)
    result = filter_files(tmp_path)

    assert result == []
