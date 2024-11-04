import logging
import os
import json
import shutil

from flask import Blueprint, abort, request, jsonify
from git import Repo, GitCommandError
from datetime import datetime

from services.fake_preprocess import Fake_preprocessor
from database.database import Database

db = Database()

routes = Blueprint('routes', __name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@routes.route("/initialization", methods = ["POST"])
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

    # Extract and validate repository information
    repo_info = extract_and_validate_repo_info(data)

    repo_dir = os.path.join('repos', repo_info['owner'], repo_info['repo_name'])

    # Clone the repository (purge if exists)
    try:
        clone_repo(repo_info['repo_url'], repo_dir)
    except GitCommandError as e:
        abort(500, description=f'Git error: {e}')

    # Compute embeddings
    embeddings = Fake_preprocessor.preprocess_files(repo_dir)
    embeddings_document = {
        'repo_name': repo_info['repo_name'],
        'owner': repo_info['owner'],
        'commit_sha': repo_info['latest_commit_sha'],
        'embeddings': embeddings,
        'stored_at': datetime.now().isoformat() + 'Z'
    }

    # Store embeddings
    store_embeddings(embeddings_document)

    # Optionally delete the repo directory after processing
    # shutil.rmtree(repo_dir)
    # logger.info(f"Deleted repository directory: {repo_dir}")
    logger.info('Embeddings stored successfully.')

    return jsonify({"message": "Embeddings computed and stored"}), 200

@routes.route('/report', methods = ["POST"])
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

    # Extract and validate repository information
    repo_info = extract_and_validate_repo_info(data)

    # Retrieve the stored SHA
    stored_commit_sha = retrieve_stored_sha(repo_info['owner'], repo_info['repo_name'])

    if stored_commit_sha == repo_info['latest_commit_sha']:
        logger.info('Embeddings are up to date.')
        return jsonify({"message": "Embeddings are up to date"}), 200
    else:
        logger.info('Embeddings are outdated. Recomputing embeddings.')

        repo_dir = os.path.join('repos', repo_info['owner'], repo_info['repo_name'])

        # Clone the repository (purge if exists)
        try:
            clone_repo(repo_info['repo_url'], repo_dir)
        except GitCommandError as e:
            abort(500, description=f'Git error: {e}')

        # Compute embeddings
        embeddings = Fake_preprocessor.preprocess_files(repo_dir)
        embeddings_document = {
            'repo_name': repo_info['repo_name'],
            'owner': repo_info['owner'],
            'commit_sha': repo_info['latest_commit_sha'],
            'embeddings': embeddings,
            'stored_at': datetime.now().isoformat() + 'Z'
        }

        # Store embeddings
        store_embeddings(embeddings_document)

        # Optionally delete the repo directory after processing
        # shutil.rmtree(repo_dir)
        # logger.info(f"Deleted repository directory: {repo_dir}")

        return jsonify({"message": "Embeddings recomputed and updated"}), 200
    
def clone_repo(repo_url, repo_dir):
    """
    Clones the repository. If the repository directory already exists, it is purged before cloning.

    :param repo_url: The URL of the repository to clone.
    :param repo_dir: The directory where the repository will be cloned.
    :return: None
    :raises: GitCommandError if cloning fails.
    """
    logger.debug(f"Cloning repository from {repo_url} to {repo_dir}.")

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

    :param owner: The repository owner's username.
    :param repo_name: The repository name.
    :return: The latest commit SHA or None if not found.
    """
    logger.debug(f"Fetching latest SHA for {owner}/{repo_name} from file.")

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
                        logger.debug(f"Found matching record: {record}")
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

    :param embeddings_document: The embeddings data to store.
    :return: None
    :raises: Exception if writing to the file fails.
    """
    logger.debug("Storing embeddings in local file.")

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

        logger.info('Embeddings stored in text file successfully.')
    except Exception as e:
        logger.error(f"Failed to write to embeddings records file: {e}")
        raise

def extract_and_validate_repo_info(data):
    """
    Extracts and validates repository information from the incoming request data.

    :param data: The JSON data from the request.
    :return: A dictionary containing repository information.
    :raises: aborts the request with a 400 error if validation fails.
    """
    logger.debug("Extracting and validating repository information.")

    # Extract repository information from data
    repo_url = data.get('repo_url')
    owner = data.get('owner')
    repo_name = data.get('repo_name')
    default_branch = data.get('default_branch')
    latest_commit_sha = data.get('latest_commit_sha')

    # Validate required fields
    if not all([repo_url, owner, repo_name, default_branch, latest_commit_sha]):
        logger.error("Missing required repository information.")
        abort(400, description="Missing required repository information")

    repo_info = {
        'repo_url': repo_url,
        'owner': owner,
        'repo_name': repo_name,
        'default_branch': default_branch,
        'latest_commit_sha': latest_commit_sha
    }

    logger.debug(f"Validated repository information: {repo_info}")
    return repo_info


def store_embeddings(embeddings_document):
    """
    Stores the embeddings document in the database or local file.

    :param embeddings_document: The embeddings data to store.
    :return: None
    :raises: aborts the request with a 500 error if storage fails.
    """
    logger.debug("Storing embeddings.")

    if db.USE_MONGODB:
        try:
            # Use update_one with upsert=True to ensure only one document per repo
            db.get_embeddings_collection().update_one(
                {'repo_name': embeddings_document['repo_name'], 'owner': embeddings_document['owner']},
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


def retrieve_stored_sha(owner, repo_name):
    """
    Retrieves the stored commit SHA for the specified repository.

    :param owner: The repository owner's username.
    :param repo_name: The repository name.
    :return: The stored commit SHA or None if not found.
    :raises: aborts the request with a 500 error if retrieval fails.
    """
    logger.debug(f"Retrieving stored SHA for {owner}/{repo_name}.")

    stored_commit_sha = None
    if db.USE_MONGODB:
        try:
            existing_embedding = db.get_embeddings_collection().find_one(
                {'repo_name': repo_name, 'owner': owner},
                sort=[('stored_at', -1)]  # Get the latest record
            )
            if existing_embedding:
                stored_commit_sha = existing_embedding.get('commit_sha')
                logger.debug(f"Retrieved stored SHA: {stored_commit_sha}")
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            abort(500, description="Database query failed.")
    else:
        # Retrieve the latest SHA from the local file
        stored_commit_sha = get_latest_sha_from_file(owner, repo_name)
        logger.debug(f"Retrieved stored SHA from file: {stored_commit_sha}")

    return stored_commit_sha