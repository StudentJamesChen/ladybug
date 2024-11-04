import re
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import wordpunct_tokenize

class Preprocessor:
    def camel_case_split(identifier):
        """
        Splits camelCase words via regular expression

        Args:
            identifier (string): token to be matched

        Returns:
            list: split tokens
        """

        matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
        return [m.group(0) for m in matches]
    
    def tokenize_text(text):
        """
        Tokenizes the text into individual words
        Splits camelCase words
        Removes cases

        Args:
            text (string): string to be tokenized

        Returns:
            list: tokens
        """

        tokens = []

        # Tokenize the input text
        for token in wordpunct_tokenize(text):
            for word in Preprocessor.camel_case_split(token):
                tokens.append(word)

        # Remove short tokens
        tokens = [token for token in tokens if len(token) > 2]

        return tokens
    
    def remove_special_characters(text):
        """
        Removes special characters and punctuation from input text

        Args:
            text (string): string to have special chars removed 

        Returns:
            text (string): new string with special chars removed
        """
        
        # Replace escape character with a ' '
        text = text.replace("\n", " ")

        # Replace special characters and numbers with a ' '
        text = re.sub("[^A-Za-z\s]+", " ", text)
        return text
    
    def preprocess_text(text, stop_words_path):
        """
        Preprocesses input text by
            - Removing Numbers
            - Removing special characters
            - Removing punctuation
            - Removing tokens of size 1-2
            - Removing cases
            - Removing inputted stop words

        Args:
            text (string): text to be preprocessed
            stop_words (string): path to a stop words file

        Returns:
            string: preprocessed text
        """

        # Remove all special chars and punctuation from the text
        text = Preprocessor.remove_special_characters(text)

        # Tokenize the text
        tokens = Preprocessor.tokenize_text(text)

        try:
            # Read stop words from the input
            with open(stop_words_path) as f:
                stop_words = set(f.read().splitlines())
        except OSError as e:
            return FileNotFoundError


        # Remove stop words
        tokens = [token for token in tokens if token not in stop_words]

        # Lemmatize the tokens. i.e., running -> run
        lemmatizer = WordNetLemmatizer();
        tokens = [lemmatizer.lemmatize(token) for token in tokens]

        # Join the tokens into a single string and remove cases
        preprocessed_text = " ".join(tokens).lower()

        return preprocessed_text
