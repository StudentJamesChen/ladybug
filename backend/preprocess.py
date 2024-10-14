import os
import zipfile

class Preprocessor:
    @staticmethod
    def preprocess_files(zip_file_path: str):
        extract_dir = 'extracted_repo'
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        files_list = []
        for dirpath, dirnames, filenames in os.walk(extract_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                files_list.append(file_path)

        print("Extracted and processed files:", files_list)