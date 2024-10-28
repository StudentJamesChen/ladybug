from dotenv import find_dotenv, load_dotenv
from flask import Flask, abort, request, jsonify
from preprocess import Preprocessor
import os
from git import Repo, GitCommandError
import logging
from pymongo import MongoClient
import json
import shutil

# Load environment variables
load_dotenv(find_dotenv())
password = os.environ.get("MONGOPASSWORD")

app = Flask(__name__)

# Configuration Flag: Set to True for dev mode (no db access. pulls from EXAMPLE_DATA.json)
USE_TEST_DATA = True

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB connection
USE_DATABASE = False
embeddings_collection = None

if not USE_TEST_DATA:
    try:
        connection_string = f"mongodb+srv://samarkaranch:{password}@cluster0.269ml.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(connection_string)
        dbs = client.list_database_names()
        test_db = client.test
        embeddings_collection = test_db.embeddings
        logger.info("Connected to MongoDB successfully.")
        USE_DATABASE = True
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        client = None

@app.route("/", methods=["GET", "POST"])
def index():
    abort(400, description="Bad Request")

@app.route("/preprocess", methods=["POST"])
def preprocess():
    data = None

    if USE_TEST_DATA:
        try:
            with open("EXAMPLE_DATA.json", "r") as test_file:
                data = json.load(test_file)
            logger.info("Loaded test data from EXAMPLE_DATA.json.")
        except FileNotFoundError:
            logger.error("EXAMPLE_DATA.json not found.")
            abort(500, description="Test data file not found.")
        except json.JSONDecodeError:
            logger.error("Invalid JSON in EXAMPLE_DATA.json.")
            abort(500, description="Invalid JSON in test data file.")
    else:
        data = request.get_json()
        if not data:
            abort(400, description="Invalid JSON data")
    print(data)
    # Extract repository information
    repo_url = data.get('repo_url')
    owner = data.get('owner')
    repo_name = data.get('repo_name')
    default_branch = data.get('default_branch')
    latest_commit_sha = data.get('latest_commit_sha')

    # Validate required fields
    if not all([repo_url, owner, repo_name, default_branch, latest_commit_sha]):
        abort(400, description="Missing required repository information")

    # Check if embeddings already exist
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
        logger.info('Embeddings for this commit SHA already exist.')
        return jsonify({"message": "Embeddings are up to date"}), 200

    repo_dir = os.path.join('repos', owner, repo_name)

    # Remove existing repository directory if it exists
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
        logger.info(f"Removed existing repository directory: {repo_dir}")

    # Clone the repository
    try:
        logger.info('Cloning the repository...')
        repo = Repo.clone_from(repo_url, repo_dir)
        logger.info('Repository cloned successfully.')
    except GitCommandError as e:
        logger.error(f'Git error: {e}')
        abort(500, description=f'Git error: {e}')

    # Compute embeddings
    embeddings = Preprocessor.preprocess_files(repo_dir)
    embeddings_document = {
        'repo_name': repo_name,
        'owner': owner,
        'commit_sha': latest_commit_sha,
        'embeddings': embeddings  # Ensure this is serializable
    }

    # Store embeddings
    if USE_DATABASE:
        try:
            embeddings_collection.insert_one(embeddings_document)
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

def check_embeddings_in_file(owner, repo_name, commit_sha):
    filename = 'embeddings_records.txt'
    if not os.path.exists(filename):
        logger.info(f"Embeddings records file {filename} does not exist.")
        return False
    try:
        with open(filename, 'r') as file:
            for line in file:
                try:
                    record = json.loads(line)
                    if (record['owner'] == owner and
                            record['repo_name'] == repo_name and
                            record['commit_sha'] == commit_sha):
                        return True
                except json.JSONDecodeError:
                    logger.warning("Encountered invalid JSON record in embeddings_records.txt.")
                    continue
    except Exception as e:
        logger.error(f"Error reading embeddings records file: {e}")
    return False

def store_embeddings_in_file(embeddings_document):
    filename = 'embeddings_records.txt'
    try:
        with open(filename, 'a') as file:
            json_record = json.dumps({
                'owner': embeddings_document['owner'],
                'repo_name': embeddings_document['repo_name'],
                'commit_sha': embeddings_document['commit_sha'],
                # Storing a placeholder to keep the file size manageable during testing
                'embeddings': 'embeddings_data_placeholder'
            })
            file.write(json_record + '\n')
    except Exception as e:
        logger.error(f"Failed to write to embeddings records file: {e}")
        raise

if __name__ == "__main__":
    app.run(port=5000, debug=True)
