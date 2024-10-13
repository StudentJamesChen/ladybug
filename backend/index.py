from dotenv import find_dotenv, load_dotenv
from flask import Flask, abort
from flask import request
import json
from preprocess import Preprocessor
import os
import pprint
from pymongo import MongoClient

load_dotenv(find_dotenv())
password = os.environ.get("MONGOPASSWORD")

app = Flask(__name__)
connection_string = f"mongodb+srv://samarkaranch:{password}@cluster0.269ml.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(connection_string)
dbs = client.list_database_names()
test_db = client.test

@app.route("/", methods=["GET","POST"])
def index():
    abort(400)

@app.route("/preprocess", methods=["POST"])
def preprocess():
    filepath = json.loads(request.data)['path']
    app.logger.info(filepath)
    if not filepath:
        abort(401)

    app.logger.info(f"Preprocessing repository {filepath}...")

    Preprocessor.preprocess_files(filepath)

    return {
        "message": "success"
    }


if __name__ == "__main__":
    app.run(port=5000, debug=True)