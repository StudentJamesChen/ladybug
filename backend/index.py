import logging

from flask import Flask, jsonify
from dotenv import find_dotenv, load_dotenv

from app.api.routes import routes
from database.database import Database

# Load environment variables
load_dotenv(find_dotenv())

def create_app(test_config=None):
    password = os.environ.get("MONGOPASSWORD")

    app = Flask(__name__)
    app.register_blueprint(routes)

    # Initializes the client
    db = Database()
    db.initialize_mongo()
    client = db.get_client()

    # Configuration Flag: Add USE_DATABASE="False" to your .env to use local file database
    db.USE_DATABASE = os.environ.get("USE_DATABASE", "True").lower() == "true"

    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize MongoDB connection
    embeddings_collection = None

    if db.USE_DATABASE:
        try:
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
    
    # Apply test-specific configurations if any
    if test_config:
        app.config.update(test_config)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(port=5000, debug=True)