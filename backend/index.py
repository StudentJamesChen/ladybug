import logging

from flask import Flask, jsonify
from dotenv import find_dotenv, load_dotenv

from app.api.routes import routes
from database.database import Database

# Load environment variables
load_dotenv(find_dotenv())

# Set up flask framework and routing
app = Flask(__name__)
app.register_blueprint(routes) 

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    return jsonify({"message": "Hello, world!"}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=False)
    
    # Initializes the database client
    db = Database('test', 'repos', 'embeddings')