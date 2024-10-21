import os

class Preprocessor:
    @staticmethod
    def preprocess_files(repo_dir: str):
        embeddings = []
        for dirpath, dirnames, filenames in os.walk(repo_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                # For testing, return dummy embedding data. This is where we implement unixcoder logic.
                embedding = {'file_path': file_path, 'embedding': 'dummy_embedding'}
                embeddings.append(embedding)
        print("Processed files and generated dummy embeddings.")
        return embeddings
