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

