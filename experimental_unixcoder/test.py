# This example code is from https://github.com/microsoft/CodeBERT/blob/master/UniXcoder/README.md

import torch
from unixcoder import UniXcoder

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = UniXcoder("microsoft/unixcoder-base")
model.to(device)

# Encode maximum function 
# Imagine this is one file
func = "def f(a,b): if a>b: return a else return b"
tokens_ids = model.tokenize([func],max_length=512,mode="<encoder-only>")
source_ids = torch.tensor(tokens_ids).to(device)
tokens_embeddings,max_func_embedding = model(source_ids)

# Encode minimum function
# Imagine this is another file
func = "def f(a,b): if a<b: return a else return b"
tokens_ids = model.tokenize([func],max_length=512,mode="<encoder-only>")
source_ids = torch.tensor(tokens_ids).to(device)
tokens_embeddings,min_func_embedding = model(source_ids)

# Encode NL
# Imagine this is the bug report
nl = "return maximum value"
tokens_ids = model.tokenize([nl],max_length=512,mode="<encoder-only>")
source_ids = torch.tensor(tokens_ids).to(device)
tokens_embeddings,nl_embedding = model(source_ids)

print(max_func_embedding.shape)
print(max_func_embedding)

# Normalize embedding
norm_max_func_embedding = torch.nn.functional.normalize(max_func_embedding, p=2, dim=1)
norm_min_func_embedding = torch.nn.functional.normalize(min_func_embedding, p=2, dim=1)
norm_nl_embedding = torch.nn.functional.normalize(nl_embedding, p=2, dim=1)

max_func_nl_similarity = torch.einsum("ac,bc->ab",norm_max_func_embedding,norm_nl_embedding)
min_func_nl_similarity = torch.einsum("ac,bc->ab",norm_min_func_embedding,norm_nl_embedding)

# The closer the cosine similarity value is to 1, the more similar the vectors are
# The maximum function / file is higher rated because we looked for "return maximum value"
print(max_func_nl_similarity)
print(min_func_nl_similarity)