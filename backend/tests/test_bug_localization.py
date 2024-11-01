from unittest.mock import Mock
import torch
import os

from bug_localization import BugLocalization
from bug_localization.unixcoder import UniXcoder

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = UniXcoder("microsoft/unixcoder-base")
mock_buglocalization = BugLocalization(device=device, model=model)

def test_ranking():
    query_embedding = get_query_embedding()
    db_embeddings = get_db_embeddings()
    similarities = mock_buglocalization.rank_files(query_embedding, db_embeddings)
    assert similarities[0][0] == db_embeddings[0][0]

def get_query_embedding():
    if not os.path.exists('query.pt'):
        torch.save(create_text_embedding('return maximum value'), 'query.pt')
    return torch.load('query.pt')

def get_db_embeddings():
    ids = ['text1', 'text2']
    embeddings = []

    if not os.path.exists('db/'):
        os.mkdir('db/')
        texts = ["def f(a,b): if a>b: return a else return b",
                 "def f(a,b): if a<b: return a else return b"]
        count = 1
        for text in texts:
            torch.save(create_text_embedding(text), f'db/embedding{count}.pt')
            count += 1
    
    for i in range(len(ids)):
        embeddings.append(torch.load(f'db/embedding{i+1}.pt'))

    return list(zip(ids, embeddings))

def create_text_embedding(text):
    tokens_ids = model.tokenize([text], max_length=512, mode="<encoder-only>")
    source_ids = torch.tensor(tokens_ids).to(device)
    _, embedding = model(source_ids)
    norm_embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
    return norm_embedding