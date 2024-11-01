import os
from dotenv import find_dotenv, load_dotenv
from pymongo import MongoClient

class Database:
    _instance = None  # Class-level instance variable for the singleton pattern

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Load environment variables
        load_dotenv(find_dotenv())
        self.password = os.environ.get("MONGOPASSWORD")
        self.client = None  # Initialize client as None
        self.USE_DATABASE = False

    def initialize_mongo(self):
        # Create a single instance of MongoClient
        if self.client is None:
            connection_string = (
                f"mongodb+srv://samarkaranch:{self.password}@cluster0.269ml.mongodb.net/"
                "?retryWrites=true&w=majority&appName=Cluster0"
            )
            self.client = MongoClient(connection_string)

    def get_client(self):
        if self.client is None:
            self.initialize_mongo()
        return self.client
