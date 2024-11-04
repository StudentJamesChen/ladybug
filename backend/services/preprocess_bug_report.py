from backend.services.preprocess import Preprocessor

# Main driver method for preprocessing bug reports
def preprocess_bug_report(bug_report_path: str):
    """
    Preprocesses bug reports and applies query reformulation (MVP)

    Args:
        bug_report_path (str): The path to the bug report

    Returns:
        String: The preprocessed bug report
    """

    stop_words_path = "../data/stop_words/java-keywords-bugs.txt"

    # Put bug report content into a string
    try:
        with open(bug_report_path, "r") as file:
            bug_report_string = file.read()
    except FileNotFoundError:
        print(f"Error: The bug report at '{bug_report_path}' was not found.")
        return 

    # Run bug report through preprocessor
    preprocessed_bug_report = Preprocessor.preprocess_text(bug_report_string, stop_words_path)

    # Apply query reformulation (MVP)

    # Return preprocessed bug report as a string
    return preprocessed_bug_report