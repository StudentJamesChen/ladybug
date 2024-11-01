import logging
import os
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from flask import Flask, abort, request, jsonify
from git import Repo, GitCommandError
from pymongo import MongoClient

from app.api.routes import routes
from services.fake_preprocess import Fake_preprocessor

# Load environment variables
load_dotenv(find_dotenv())
password = os.environ.get("MONGOPASSWORD")

app = Flask(__name__)
app.register_blueprint(routes)

# Configuration Flag: Set to False to disable database and use local file storage
USE_DATABASE = True

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

if __name__ == "__main__":
    app.run(port=5000, debug=True)
