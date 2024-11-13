import torch
# needs absolute path to work with others

# from experimental_unixcoder.unixcoder import UniXcoder # uncomment when live
from unixcoder import UniXcoder # uncomment when testing

class BugLocalization:
    def __init__(self):
        # Set up device and initialize the UniXcoder model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("CUDA is available" if torch.cuda.is_available() else "CUDA is not available")
        self.model = UniXcoder("microsoft/unixcoder-base")
        self.model.to(self.device)

    # Encoding for Long Texts
    def encode_text(self, text):
        """
        Encodes long text by splitting it into chunks of max 512 tokens.
        Returns a list of embeddings (as lists), one for each chunk.
        """
        # Tokenize the text
        tokens = self.model.tokenize([text], mode="<encoder-only>")[0]
        print(f"Total tokens in text: {len(tokens)}")  # Debug print

        chunk_size = 512
        embeddings = []

        # Process each chunk
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            print(f"Processing chunk {i // chunk_size + 1}: tokens {i} to {i + chunk_size}")  # Debug print
            
            # Convert chunk tokens to tensor
            source_ids = torch.tensor([chunk_tokens]).to(self.device)
            
            # Get model output (adjust if model's output format differs)
            try:
                _, embedding = self.model(source_ids)
                norm_embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
                embeddings.append(norm_embedding.tolist())  # Store normalized embedding as list
            except Exception as e:
                print(f"Error processing chunk {i // chunk_size + 1}: {e}")
                continue

        return embeddings


    # File Ranking for Bug Localization
    def rank_files(self, query_embeddings, db_embeddings):
        """
        Ranks files based on similarity to the query embeddings.

        Parameters:
        - query_embeddings: A list of embeddings (as lists) for the query (bug report).
        - db_embeddings: A list of tuples, where each tuple contains (file_id, embeddings)
                         where embeddings is a list of embeddings (as lists) for that file.

        Returns:
        - A sorted list of (file_id, max_similarity_score) tuples in descending order of similarity.
        """
        similarities = []

        for file_id, file_embeddings in db_embeddings:
            max_similarity = float('-inf')

            # Convert query embeddings and file embeddings from lists back to tensors
            for query_embedding in query_embeddings:
                query_tensor = torch.tensor(query_embedding, device=self.device)
                for file_embedding in file_embeddings:
                    file_tensor = torch.tensor(file_embedding, device=self.device)

                    # Compute similarity
                    similarity = torch.nn.functional.cosine_similarity(
                        query_tensor, file_tensor, dim=1
                    ).item()

                    if similarity > max_similarity:
                        max_similarity = similarity

            similarities.append((file_id, max_similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities

if __name__ == "__main__":
    # Create an instance of the BugLocalization class
    bug_localizer = BugLocalization()
    
    # Example bug report text (long text)
    sample_text = "Your long bug report text that exceeds 512 tokens..."
    print("Encoding bug report for bug localization...")
    query_embeddings = bug_localizer.encode_text(sample_text)
    
    # Example database embeddings for files (each with long text)
    file1_text = "Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens..Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens...Contents of file 1 that is over 512 tokens..."
    file2_text = "Contents of file 2 that is over 512 tokens..."
    
    file1_embeddings = bug_localizer.encode_text(file1_text)
    print(file1_embeddings)
    file2_embeddings = bug_localizer.encode_text(file2_text)
    print(file2_embeddings)
    
    # Prepare data for MongoDB storage (embeddings as lists)
    db_embeddings = [
        ("file1", file1_embeddings),
        ("file2", file2_embeddings)
    ]
    
    # Rank files based on similarity to the query
    print("Ranking files based on similarity...")
    ranked_files = bug_localizer.rank_files(query_embeddings, db_embeddings)
    print("Ranked files:", ranked_files)
