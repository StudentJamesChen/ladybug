from flask import Flask, abort
from flask import request
import json
from preprocess import Preprocessor

app = Flask(__name__)

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