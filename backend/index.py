from dotenv import find_dotenv, load_dotenv
from flask import Flask, abort, request
from preprocess import Preprocessor
import os
from git import Repo, GitCommandError
import logging
from pymongo import MongoClient
import json

load_dotenv(find_dotenv())
password = os.environ.get("MONGOPASSWORD")

app = Flask(__name__)

# Flag to indicate if the database is available. If not, we jump into dev mode which stores embeddings in a text file.
USE_DATABASE = False
try:
    connection_string = f"mongodb+srv://samarkaranch:{password}@cluster0.269ml.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(connection_string)
    dbs = client.list_database_names()
    test_db = client.test
    app.logger.info("Connected to MongoDB successfully.")
    USE_DATABASE = True
except Exception as e:
    app.logger.error(f"Could not connect to MongoDB: {e}")
    client = None

@app.route("/", methods=["GET", "POST"])
def index():
    abort(400)

@app.route("/preprocess", methods=["POST"])
def preprocess():
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON data")

    repo_url = data.get('repo_url')
    owner = data.get('owner')
    repo_name = data.get('repo_name')
    default_branch = data.get('default_branch')
    latest_commit_sha = data.get('latest_commit_sha')

    if not repo_url or not owner or not repo_name or not default_branch or not latest_commit_sha:
        abort(400, description="Missing required repo information")

    # Check if embeddings for this commit SHA already exist
    embeddings_exist = False
    if USE_DATABASE:
        existing_embedding = embeddings_collection.find_one({
            'repo_name': repo_name,
            'owner': owner,
            'commit_sha': latest_commit_sha
        })
        if existing_embedding:
            embeddings_exist = True
    else:
        # Check a local text file
        embeddings_exist = check_embeddings_in_file(owner, repo_name, latest_commit_sha)

    if embeddings_exist:
        print('Embeddings for this commit SHA already exist.')
        return {"message": "Embeddings are up to date"}, 200

    repo_dir = os.path.join('repos', owner, repo_name)

    if os.path.exists(repo_dir):
        import shutil
        shutil.rmtree(repo_dir)

    try:
        print('Cloning the repository...')
        repo = Repo.clone_from(repo_url, repo_dir)
        print('Repository cloned successfully.')
    except GitCommandError as e:
        print(f'Git error: {e}')
        abort(500, description=f'Git error: {e}')

    # Compute embeddings
    embeddings = Preprocessor.preprocess_files(repo_dir)
    embeddings_document = {
        'repo_name': repo_name,
        'owner': owner,
        'commit_sha': latest_commit_sha,
        'embeddings': embeddings  # this should be serialized to store in the database
    }

    if USE_DATABASE:
        embeddings_collection.insert_one(embeddings_document)
        print('Embeddings stored in database successfully.')
    else:
        store_embeddings_in_file(embeddings_document)
        print('Embeddings stored in text file successfully.')

    # delete the repo directory
    # import shutil
    # shutil.rmtree(repo_dir)

    return {"message": "Embeddings computed and stored"}, 200

def check_embeddings_in_file(owner, repo_name, commit_sha):
    filename = 'embeddings_records.txt'
    if not os.path.exists(filename):
        return False
    with open(filename, 'r') as file:
        for line in file:
            try:
                record = json.loads(line)
                if (record['owner'] == owner and
                        record['repo_name'] == repo_name and
                        record['commit_sha'] == commit_sha):
                    return True
            except json.JSONDecodeError:
                continue
    return False

def store_embeddings_in_file(embeddings_document):
    filename = 'embeddings_records.txt'
    with open(filename, 'a') as file:
        json_record = json.dumps({
            'owner': embeddings_document['owner'],
            'repo_name': embeddings_document['repo_name'],
            'commit_sha': embeddings_document['commit_sha'],
            # We can skip storing actual embeddings to avoid large file sizes during testing
            'embeddings': 'embeddings_data_placeholder'
        })
        file.write(json_record + '\n')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
