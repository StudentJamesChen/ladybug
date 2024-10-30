import torch
from unixcoder import UniXcoder
# from db_client import collection  # Import the MongoDB collection from db_client

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

    # Storing Embeddings in MongoDB
    def store_embedding(self, file_id, embedding):
        """Stores a single normalized embedding in MongoDB with a unique file_id."""
        embedding_data = {"file_id": file_id, "embedding": embedding.cpu().numpy().tolist()}
        # collection.insert_one(embedding_data)

    def store_embeddings_batch(self, embeddings_dict):
        """Stores a batch of embeddings in MongoDB."""
        for file_id, embedding in embeddings_dict.items():
            self.store_embedding(file_id, embedding)

    # File Ranking for Bug Localization
    def rank_files(self, query_embedding):
        """Ranks files in MongoDB based on similarity to the query embedding."""
        # Fetch all embeddings from the database
        # db_embeddings = list(collection.find())
        
        # Normalize the query embedding
        norm_query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=1)
        
        # Calculate similarity scores
        similarities = []
        # for file in db_embeddings:
        #    db_embedding = torch.tensor(file['embedding']).to(self.device)
        #    similarity = torch.einsum("ac,bc->ab", norm_query_embedding, db_embedding).item()
        #    similarities.append((file['file_id'], similarity))
        
        # Sort files by similarity score in descending order
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
