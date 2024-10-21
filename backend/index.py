from dotenv import find_dotenv, load_dotenv
from flask import Flask, abort, request
import json
from preprocess import Preprocessor
import os
import pprint
from pymongo import MongoClient
import logging

load_dotenv(find_dotenv())
password = os.environ.get("MONGOPASSWORD")

app = Flask(__name__)

client = None
dbs = []
test_db = None

try:
    # Remove the non-database connection code once we all get credentials
    connection_string = f"mongodb+srv://samarkaranch:{password}@cluster0.269ml.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(connection_string)
    dbs = client.list_database_names()
    test_db = client.test
    app.logger.info("Connected to MongoDB successfully.")
except Exception as e:
    app.logger.warning(f"{e}\n============================\nCould not connect to MongoDB")
    client = None

@app.route("/", methods=["GET", "POST"])
def index():
    abort(400)

@app.route("/preprocess", methods=["POST"])
def preprocess():
    if request.content_type == 'application/zip':
        zipdata = request.get_data()
        filepath = 'received_repo.zip'
        with open(filepath, 'wb') as f:
            f.write(zipdata)

        Preprocessor.preprocess_files(filepath)

        return {"message": "success"}, 200
    else:
        abort(415, description="Unsupported Media Type: Expected 'application/zip'")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
