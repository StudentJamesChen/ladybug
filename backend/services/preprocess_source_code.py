import os
from backend.services.preprocess import Preprocessor

def preprocess_source_code(root):
    """
    Preprocesses all source code files in a source code repository. Assumes all files contained
    in the root directory have had non-.java files filtered out.

    Args:
        root (string): path to the root directory of the source code repository

    Returns:
        tuple (list): list of tuples mapping file name to preprocessed contents
    """

    preprocessed_files = []

    stop_words_path = "/data/stop_words/java-keywords-bugs.txt"

    # Iterate through each file/folder in the root dir
    for file_name in os.listdir(root):
        file_path = os.path.join(root, file_name)
        if(os.path.isfile(file_path)):
            # Read and preprocess source code file and append it to the outout list
            with open(file_path, "r") as f:
                file_content = f.read()
                preprocessed_file_content = Preprocessor.preprocess_text(file_content, stop_words_path)
                preprocessed_files.append((file_path, file_name, preprocessed_file_content))

    return preprocessed_files