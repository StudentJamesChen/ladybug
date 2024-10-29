import json
import logging
import os
import shutil
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from flask import Flask, abort, request, jsonify
from git import Repo, GitCommandError
from pymongo import MongoClient

from preprocess import Preprocessor

# Load environment variables
load_dotenv(find_dotenv())
password = os.environ.get("MONGOPASSWORD")

app = Flask(__name__)

# Configuration Flag: Set to False to disable database and use local file storage
USE_DATABASE = False

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB connection
embeddings_collection = None

if USE_DATABASE:
    try:
        connection_string = (
            f"mongodb+srv://samarkaranch:{password}@cluster0.269ml.mongodb.net/"
            "?retryWrites=true&w=majority&appName=Cluster0"
        )
        client = MongoClient(connection_string)
        dbs = client.list_database_names()
        test_db = client.test
        embeddings_collection = test_db.embeddings
        logger.info("Connected to MongoDB successfully.")
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        client = None
        USE_DATABASE = False  # Fallback to file storage if DB connection fails


@app.route("/", methods=["GET", "POST"])
def index():
    return jsonify({"message": "Hello, world!"}), 200


@app.route("/initialization", methods=["POST"])
def initialization():
    """
    Initialization Endpoint:
    - Clones the repository.
    - Computes embeddings.
    - Stores embeddings along with repository information and SHA.
    - Always performs a fresh setup, overwriting any existing embeddings.
    """
    # Read data from the incoming request
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON data")

    logger.info("Received data from /initialization request.")

    # Extract repository information from data
    repo_url = data.get('repo_url')
    owner = data.get('owner')
    repo_name = data.get('repo_name')
    default_branch = data.get('default_branch')
    latest_commit_sha = data.get('latest_commit_sha')

    # Validate required fields
    if not all([repo_url, owner, repo_name, default_branch, latest_commit_sha]):
        abort(400, description="Missing required repository information")

    repo_dir = os.path.join('repos', owner, repo_name)

    # Clone the repository (purge if exists)
    try:
        clone_repo(repo_url, repo_dir)
    except GitCommandError as e:
        abort(500, description=f'Git error: {e}')

    # Compute embeddings
    embeddings = Preprocessor.preprocess_files(repo_dir)
    embeddings_document = {
        'repo_name': repo_name,
        'owner': owner,
        'commit_sha': latest_commit_sha,
        'embeddings': embeddings,
        'stored_at': datetime.utcnow().isoformat() + 'Z'
    }

    # Store embeddings
    if USE_DATABASE:
        try:
            # Use update_one with upsert=True to ensure only one document per repo
            embeddings_collection.update_one(
                {'repo_name': repo_name, 'owner': owner},
                {'$set': embeddings_document},
                upsert=True
            )
            logger.info('Embeddings stored in database successfully.')
        except Exception as e:
            logger.error(f"Failed to store embeddings in database: {e}")
            abort(500, description="Failed to store embeddings in database.")
    else:
        try:
            store_embeddings_in_file(embeddings_document)
            logger.info('Embeddings stored in text file successfully.')
        except Exception as e:
            logger.error(f"Failed to store embeddings in file: {e}")
            abort(500, description="Failed to store embeddings in file.")

    # Optionally delete the repo directory after processing
    # shutil.rmtree(repo_dir)
    # logger.info(f"Deleted repository directory: {repo_dir}")

    return jsonify({"message": "Embeddings computed and stored"}), 200


@app.route("/report", methods=["POST"])
def report():
    """
    Report Endpoint:
    - Receives repository information with the latest_commit_sha.
    - Checks if the provided SHA matches the stored SHA.
    - If SHAs do not match:
        - Reclones the repository.
        - Recomputes embeddings.
        - Updates the stored embeddings and SHA.
    - If SHAs match:
        - Confirms that embeddings are up to date.
    """
    # Read data from the incoming request
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON data")

    logger.info("Received data from /report request.")

    # Extract repository information from data
    repo_url = data.get('repo_url')
    owner = data.get('owner')
    repo_name = data.get('repo_name')
    default_branch = data.get('default_branch')
    latest_commit_sha = data.get('latest_commit_sha')

    # Validate required fields
    if not all([repo_url, owner, repo_name, default_branch, latest_commit_sha]):
        abort(400, description="Missing required repository information")

    # Retrieve the stored SHA
    stored_commit_sha = None
    if USE_DATABASE:
        try:
            existing_embedding = embeddings_collection.find_one(
                {'repo_name': repo_name, 'owner': owner},
                sort=[('stored_at', -1)]  # Get the latest record
            )
            if existing_embedding:
                stored_commit_sha = existing_embedding.get('commit_sha')
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            abort(500, description="Database query failed.")
    else:
        # Retrieve the latest SHA from the local file
        stored_commit_sha = get_latest_sha_from_file(owner, repo_name)

    if stored_commit_sha == latest_commit_sha:
        logger.info('Embeddings are up to date.')
        return jsonify({"message": "Embeddings are up to date"}), 200
    else:
        logger.info('Embeddings are outdated. Recomputing embeddings.')

        repo_dir = os.path.join('repos', owner, repo_name)

        # Clone the repository (purge if exists)
        try:
            clone_repo(repo_url, repo_dir)
        except GitCommandError as e:
            abort(500, description=f'Git error: {e}')

        # Compute embeddings
        embeddings = Preprocessor.preprocess_files(repo_dir)
        embeddings_document = {
            'repo_name': repo_name,
            'owner': owner,
            'commit_sha': latest_commit_sha,
            'embeddings': embeddings,
            'stored_at': datetime.utcnow().isoformat() + 'Z'
        }

        # Store embeddings
        if USE_DATABASE:
            try:
                # Use update_one with upsert=True to ensure only one document per repo
                embeddings_collection.update_one(
                    {'repo_name': repo_name, 'owner': owner},
                    {'$set': embeddings_document},
                    upsert=True
                )
                logger.info('Embeddings updated in database successfully.')
            except Exception as e:
                logger.error(f"Failed to update embeddings in database: {e}")
                abort(500, description="Failed to update embeddings in database.")
        else:
            try:
                store_embeddings_in_file(embeddings_document)
                logger.info('Embeddings updated in text file successfully.')
            except Exception as e:
                logger.error(f"Failed to update embeddings in file: {e}")
                abort(500, description="Failed to update embeddings in file.")

        # Optionally delete the repo directory after processing
        # shutil.rmtree(repo_dir)
        # logger.info(f"Deleted repository directory: {repo_dir}")

        return jsonify({"message": "Embeddings recomputed and updated"}), 200


def clone_repo(repo_url, repo_dir):
    """
    Clones the repository. If the repository directory already exists, it is purged before cloning.
    """
    if os.path.exists(repo_dir):
        logger.info(f"Repository directory {repo_dir} exists. Purging for fresh clone.")
        shutil.rmtree(repo_dir)

    try:
        Repo.clone_from(repo_url, repo_dir)
        logger.info('Repository cloned successfully.')
    except GitCommandError as e:
        logger.error(f"Failed to clone repository: {e}")
        raise


def get_latest_sha_from_file(owner, repo_name):
    """
    Retrieves the latest commit SHA for the specified repository from the local embeddings_records.txt file.
    """
    filename = 'embeddings_records.txt'
    if not os.path.exists(filename):
        logger.info(f"Embeddings records file {filename} does not exist.")
        return None
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            for line in reversed(lines):  # Start from the end for the latest entry
                try:
                    record = json.loads(line)
                    if (record['owner'] == owner and
                            record['repo_name'] == repo_name):
                        return record.get('commit_sha')
                except json.JSONDecodeError:
                    logger.warning("Encountered invalid JSON record in embeddings_records.txt.")
                    continue
    except Exception as e:
        logger.error(f"Error reading embeddings records file: {e}")
    return None


def store_embeddings_in_file(embeddings_document):
    """
    Stores the embeddings document in the local embeddings_records.txt file.
    Overwrites existing embeddings for the repository to ensure a fresh update.
    """
    filename = 'embeddings_records.txt'
    try:
        # Read existing records
        records = {}
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                for line in file:
                    try:
                        record = json.loads(line)
                        key = (record['owner'], record['repo_name'])
                        records[key] = record
                    except json.JSONDecodeError:
                        logger.warning("Encountered invalid JSON record in embeddings_records.txt.")
                        continue

        # Update the record for the current repository
        key = (embeddings_document['owner'], embeddings_document['repo_name'])
        records[key] = {
            'owner': embeddings_document['owner'],
            'repo_name': embeddings_document['repo_name'],
            'commit_sha': embeddings_document['commit_sha'],
            'embeddings': embeddings_document['embeddings'],
            'stored_at': embeddings_document['stored_at']
        }

        # Write all records back to the file
        with open(filename, 'w') as file:
            for record in records.values():
                json_record = json.dumps(record)
                file.write(json_record + '\n')

    except Exception as e:
        logger.error(f"Failed to write to embeddings records file: {e}")
        raise


if __name__ == "__main__":
    app.run(port=5000, debug=True)
