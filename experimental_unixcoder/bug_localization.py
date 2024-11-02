# https://github.com/microsoft/CodeBERT/blob/master/UniXcoder/README.md
import torch
from unixcoder import UniXcoder

class BugLocalization:
    def __init__(self):
        # Set up device and initialize the UniXcoder model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = UniXcoder("microsoft/unixcoder-base")
        self.model.to(self.device)

    # Encoding Embeddings
    def encode_text(self, text):
        """Encodes a single text (bug report or function) into an embedding."""
        tokens_ids = self.model.tokenize([text], max_length=512, mode="<encoder-only>")
        source_ids = torch.tensor(tokens_ids).to(self.device)
        _, embedding = self.model(source_ids)
        norm_embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
        return norm_embedding

    def encode_batch(self, texts):
        """Encodes a batch of texts into embeddings."""
        embeddings = []
        for text in texts:
            embeddings.append(self.encode_text(text))
        return embeddings

    # File Ranking for Bug Localization
    def rank_files(self, query_embedding, db_embeddings):
        """
        Ranks files based on similarity to the query embedding.
        
        Parameters:
        - query_embedding: The embedding of the bug report or query.
        - db_embeddings: A list of tuples, where each tuple contains (file_id, embedding)
                         representing the file's unique identifier and its precomputed embedding.
                         
        Returns:
        - A sorted list of (file_id, similarity_score) tuples in descending order of similarity.
        """
        # Normalize the query embedding
        norm_query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=1)
        
        # Calculate similarity scores
        similarities = []
        for file_id, embedding in db_embeddings:
            # Ensure db_embedding is on the same device
            db_embedding = embedding.to(self.device)
            similarity = torch.einsum("ac,bc->ab", norm_query_embedding, db_embedding).item()
            similarities.append((file_id, similarity))
        
        # Sort files by similarity score in descending order
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities

# Main function that runs if the script is executed directly
if __name__ == "__main__":
    # Create an instance of the BugLocalization class
    bug_localizer = BugLocalization()
    
    # Example usage
    sample_text = "Example bug report text."
    print("Encoding text for bug localization...")
    query_embedding = bug_localizer.encode_text(sample_text)
    
    # Example database embeddings (list of tuples with file_id and embedding)
    file1_embedding = bug_localizer.encode_text("app crash incorrect secret enter general information app version app source built from source android version android custom rom emulator same crash actual device with app and from droid expect result what expect error message displayed what happen instead app crash logcat org shadowice flocke andotp dev android runtime fatal exception main process org shadowice flocke andotp dev pid java lang illegal argument exception last encode character before the padding any valid base alphabet but not possible value expect the discard bit zero org apache common codec binary base validate character base java org apache common codec binary base decode base java org apache common codec binary base codec decode base codec java org apache common codec binary base codec decode base codec java org shadowice flocke andotp database entry init entry java org shadowice flocke andotp dialog manual entry dialog click manual entry dialog java com android internal app alert controller button handler handle message alert controller java android handler dispatch message handler java android looper loop looper java android app activity thread main activity thread java java lang reflect method invoke native method com android internal runtime init method and args caller run runtime init java com android internal zygote init main zygote init java step reproduce open entry creation dialog enter detail enter test the secret field and fill other require field press save")
    file2_embedding = bug_localizer.encode_text("Function in file 2")
    db_embeddings = [
        ("file1", file1_embedding),
        ("file2", file2_embedding)
    ]
    
    # Print the embedding for "file1"
    print("Embedding for file1:", file1_embedding)
    
    # Rank files based on similarity to the query
    print("Ranking files based on similarity...")
    ranked_files = bug_localizer.rank_files(query_embedding, db_embeddings)
    print("Ranked files:", ranked_files)
