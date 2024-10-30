"""
Pseudocode:
    1. Read stop words
    2. Set constants
        a. Screen number
        b. Source code file path
    3. Get bug report path
    4. Put bug report content into string
    5. Call processBugReport()
        a. Call preprocessText()
            a. Set options for preprocessing
            b. Prep sentences
                a. Split content into sentences
                b. Apply preprocessing options to each sentenc
                c. Remove stop words
            c. Extract tokens from prepped sentences
            d. Join lemmatized tokens into a single string delimited with a space
        b. Write preprocessed bug report to text file
"""

# Main driver method for preprocessing bug reports
def preprocess_bug_report(bug_report_path: str):
    """
    Preprocesses bug reports and applies query reformulation (MVP)

    Args:
        bug_report_path (str): The path to the bug report

    Returns:
        String: The preprocessed bug report
    """

    stop_words_path = "stop_words/java-keywords-bugs.txt"

    # Put bug report content into a string
    try:
        with open(bug_report_path, "r") as file:
            bug_report_string = file.read()
    except FileNotFoundError:
        print(f"Error: The bug report at '{bug_report_path}' was not found.")
        return 

    # Run bug report through preprocessor [PENDING TERRY'S IMPLEMENTATION]
    preprocessed_bug_report = preprocessText(bug_report_string, stop_words_path)

    # Apply query reformulation (MVP)

    # Return preprocessed bug report as a string
