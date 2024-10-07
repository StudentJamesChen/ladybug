import os
from os import walk
from zipfile import ZipFile
from werkzeug.datastructures import FileStorage

class Preprocessor:
    def preprocess_files(filepath: str):
        filesList = []
        for (dirpath, dirnames, filenames) in walk(filepath):
            filesList.extend(filenames)
        print(filesList)

if __name__ == "__main__":
    exit(-1)