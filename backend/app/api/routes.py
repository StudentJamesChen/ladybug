import logging
import os
import json
import shutil

from flask import Blueprint, abort, request, jsonify
from git import Repo, GitCommandError
from datetime import datetime

from services.fake_preprocess import Fake_preprocessor
from database.database import Database
from services.preprocess_bug_report import preprocess_bug_report
from services.preprocess_source_code import preprocess_source_code
from services.filter import filter_files
from experimental_unixcoder.bug_localization import BugLocalization

# Initialize Database
db = Database()
db.initialize_mongo()
client = db.get_client()
test_db = client.test
embeddings_collection = test_db.embeddings

# Initialize Blueprint for Routes
routes = Blueprint('routes', __name__)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ======================================================================================================================
# Routes
# ======================================================================================================================

@routes.route("/initialization", methods=["POST"])
def initialization():
    """
    Initialization Endpoint:
    - Clones the repository.
    - Computes embeddings.
    - Stores embeddings along with repository information and SHA.
    - Always performs a fresh setup, overwriting any existing embeddings.
    """
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON data")

    logger.info("Received data from /initialization request.")

    repo_info = extract_and_validate_repo_info(data)

    try:
        process_and_store_embeddings(repo_info)
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        abort(500, description=str(e))

    logger.info('Embeddings stored successfully.')
    return jsonify({"message": "Embeddings computed and stored"}), 200


@routes.route('/report', methods=["POST"])
def report():
    """
    Report Endpoint:
    - Receives repository information with the latest_commit_sha.
    - Writes the 'issue' to ./reports/repo_name/report.txt.
    - Preprocesses the bug report.
    - Checks if the provided SHA matches the stored SHA.
    - If SHAs do not match:
        - Reclones the repository.
        - Recomputes embeddings.
        - Updates the stored embeddings and SHA.
    - If SHAs match:
        - Confirms that embeddings are up to date.
    """
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON data")

    repository = data.get('repository')
    issue = data.get('issue')
    if not repository or not issue:
        abort(400, description="Missing 'repository' or 'issue' in the data")

    logger.info("Received data from /report request.")

    # Extract and validate repository information
    repo_info = extract_and_validate_repo_info(repository)

    # Write issue to report file
    try:
        report_file_path = write_file_for_report_processing(repo_info['repo_name'], issue)
    except Exception as e:
        logger.error(f"Failed to write issue to file: {e}")
        abort(500, description="Failed to write issue to file")

    try:
        preprocessed_bug_report = preprocess_bug_report(report_file_path)
        logger.info(f"Preprocessed bug report: {preprocessed_bug_report}")
    except Exception as e:
        logger.error(f"Failed to preprocess bug report: {e}")
        abort(500, description="Failed to preprocess bug report")

    # Compute Bug Report Embeddings Here

    # Retrieve the stored SHA
    stored_commit_sha = retrieve_stored_sha(repo_info['owner'], repo_info['repo_name'])

    # Check if embeddings are up to date
    if stored_commit_sha == repo_info['latest_commit_sha']:
        logger.info('Embeddings are up to date.')
        return jsonify({"message": "Embeddings are up to date"}), 200
    else:
        logger.info('Embeddings are outdated. Recomputing embeddings.')
        try:
            process_and_store_embeddings(repo_info)
        except Exception as e:
            logger.error(f"Failed to recompute embeddings: {e}")
            abort(500, description=str(e))

        return jsonify({"message": "Embeddings recomputed and updated"}), 200


# ======================================================================================================================
# Helper Functions
# ======================================================================================================================

def process_and_store_embeddings(repo_info):
    """
    Processes the repository by cloning, computing embeddings, and storing them. Always performs a fresh setup.

    :param repo_info: Dictionary containing repository information.
    """
    repo_dir = os.path.join('repos', repo_info['owner'], repo_info['repo_name'])

    clone_repo(repo_info['repo_url'], repo_dir)


    filtered_files = filter_files(repo_dir)
    for file in filtered_files:
        logger.info(f"Filtered file: {file}")

    if not filtered_files:
        logger.error("No Java files found in repository.")
        raise ValueError("No Java files found in repository.")

    # Preprocess the source code files
    preprocessed_files = preprocess_source_code(repo_dir)
    for file in preprocessed_files:
        logger.info(f"Preprocessed file: {file}")

    # Store embeddings
    clean_paths = clean_embedding_paths_for_db(preprocessed_files, repo_dir)
    embeddings_document = {
        'repo_name': repo_info['repo_name'],
        'owner': repo_info['owner'],
        'commit_sha': repo_info['latest_commit_sha'],
        'embeddings': clean_paths,
        'stored_at': datetime.utcnow().isoformat() + 'Z'
    }
    store_embeddings(embeddings_document)

    # Delete the repo directory after processing
    # shutil.rmtree(repo_dir)
    # logger.info(f"Deleted repository directory: {repo_dir}")

def clean_embedding_paths_for_db(preprocessed_files, repo_dir):
    """
    Cleans up the file paths for the database by removing the repo_dir prefix.

    :param preprocessed_files: List of preprocessed file tuples.
    :param repo_dir: The directory of the repository.
    """

    # This converts it into an easily printable form and removes the repo_dir prefix
    clean_files = []
    for file in preprocessed_files:
        embedding_text = BugLocalization.encode_text(file[2])
        clean_file = {
            'path': str(file[0]).replace(repo_dir + '/', ''),
            'name': file[1],
            'content': file[2],
            'embedding_text': embedding_text
        }
        clean_files.append(clean_file)
    return clean_files

def clone_repo(repo_url, repo_dir):
    """
    Clones the repository. If the repository directory already exists, it is purged before cloning.

    :param repo_url: The URL of the repository to clone.
    :param repo_dir: The directory where the repository will be cloned.
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


def write_file_for_report_processing(repo_name, issue_content):
    """
    Writes the issue content to a report file in the specified repository's report directory.

    :param repo_name: The name of the repository.
    :param issue_content: The content of the issue to write.
    :return: The path to the report file.
    :raises: Exception if writing to the file fails.
    """
    reports_dir = os.path.join('reports', repo_name)
    os.makedirs(reports_dir, exist_ok=True)  # Create the directory if it doesn't exist

    report_file_path = os.path.join(reports_dir, 'report.txt')
    try:
        with open(report_file_path, 'w', encoding='utf-8') as report_file:
            report_file.write(issue_content)
        logger.info(f"Issue written to {report_file_path}.")
        return report_file_path
    except Exception as e:
        logger.error(f"Failed to write issue to file: {e}")
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
        missing = [field for field in ['repo_url', 'owner', 'repo_name', 'default_branch', 'latest_commit_sha']
                   if not data.get(field)]
        logger.error(f"Missing required repository information: {', '.join(missing)}")
        abort(400, description=f"Missing required repository information: {', '.join(missing)}")

    repo_info = {
        'repo_url': repo_url,
        'owner': owner,
        'repo_name': repo_name,
        'default_branch': default_branch,
        'latest_commit_sha': latest_commit_sha
    }

    logger.debug(f"Validated repository information: {repo_info}")
    return repo_info


# ======================================================================================================================
# Handler Methods
# ======================================================================================================================

def store_embeddings(embeddings_document):
    """
    Stores the embeddings document in the database or local file.

    :param embeddings_document: The embeddings data to store.
    :raises: Aborts the request with a 500 error if storage fails.
    """
    logger.debug("Storing embeddings.")

    if db.USE_DATABASE:
        try:
            store_embeddings_in_db(embeddings_document)
        except Exception:
            abort(500, description="Failed to store embeddings in database.")
    else:
        try:
            store_embeddings_in_file_database(embeddings_document)
        except Exception:
            abort(500, description="Failed to store embeddings in file.")


def retrieve_stored_sha(owner, repo_name):
    """
    Retrieves the stored commit SHA for the specified repository.

    :param owner: The repository owner's username.
    :param repo_name: The repository name.
    :return: The stored commit SHA or None if not found.
    :raises: Aborts the request with a 500 error if retrieval fails.
    """
    logger.debug(f"Retrieving stored SHA for {owner}/{repo_name}.")

    try:
        if db.USE_DATABASE:
            stored_commit_sha = retrieve_sha_from_db(owner, repo_name)
        else:
            stored_commit_sha = get_latest_sha_from_file_database(owner, repo_name)
    except Exception:
        if db.USE_DATABASE:
            abort(500, description="Failed to retrieve commit SHA from database.")
        else:
            abort(500, description="Failed to retrieve commit SHA from file.")

    if stored_commit_sha:
        logger.debug(f"Stored commit SHA: {stored_commit_sha}")
    else:
        logger.debug("No stored commit SHA found.")

    return stored_commit_sha


# ======================================================================================================================
# Live Database (MongoDB) Methods
# ======================================================================================================================

def store_embeddings_in_db(embeddings_document):
    """
    Stores the embeddings document in the MongoDB database.

    :param embeddings_document: The embeddings data to store.
    :raises: Exception if storage fails.
    """
    logger.debug("Storing embeddings in MongoDB.")
    try:
        embeddings_collection.update_one(
            {'repo_name': embeddings_document['repo_name'], 'owner': embeddings_document['owner']},
            {'$set': embeddings_document},
            upsert=True
        )
        logger.info('Embeddings stored in database successfully.')
    except Exception as e:
        logger.error(f"Failed to store embeddings in database: {e}")
        raise


def retrieve_sha_from_db(owner, repo_name):
    """
    Retrieves the stored commit SHA for the specified repository from MongoDB.

    :param owner: The repository owner's username.
    :param repo_name: The repository name.
    :return: The stored commit SHA or None if not found.
    :raises: Exception if retrieval fails.
    """
    logger.debug(f"Retrieving stored SHA for {owner}/{repo_name} from MongoDB.")
    try:
        existing_embedding = embeddings_collection.find_one(
            {'repo_name': repo_name, 'owner': owner},
            sort=[('stored_at', -1)]  # Get the latest record
        )
        if existing_embedding:
            stored_commit_sha = existing_embedding.get('commit_sha')
            logger.debug(f"Retrieved stored SHA from database: {stored_commit_sha}")
            return stored_commit_sha
        else:
            logger.debug("No matching embedding found in database.")
            return None
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise


# ======================================================================================================================
# Local Database (File) Methods
# ======================================================================================================================

def get_latest_sha_from_file_database(owner, repo_name):
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
        with open(filename, 'r', encoding='utf-8') as file:
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


def store_embeddings_in_file_database(embeddings_document):
    """
    Stores the embeddings document in the local embeddings_records.txt file.
    Overwrites existing embeddings for the repository to ensure a fresh update.

    :param embeddings_document: The embeddings data to store.
    :raises: Exception if writing to the file fails.
    """
    logger.debug("Storing embeddings in local file.")

    filename = 'embeddings_records.txt'
    try:
        # Read existing records
        records = {}
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
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
        records[key] = embeddings_document

        # Write all records back to the file
        with open(filename, 'w', encoding='utf-8') as file:
            for record in records.values():
                json_record = json.dumps(record)
                file.write(json_record + '\n')

        logger.info('Embeddings stored in text file successfully.')
    except Exception as e:
        logger.error(f"Failed to write to embeddings records file: {e}")
        raise
