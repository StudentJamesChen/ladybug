import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class Database:
    """
    Creates (or references) the MongoDB database connection.

    :param database: The MongoDB database to access. Defaults to `'test'`.
    :param repo_collection: The repository collection name. Defaults to `'repos'`.
    :param embeddings_collection: The embeddings collection name. Defaults to `'embeddings'`.
    """
    _instance = None  # Class-level instance variable for the singleton pattern
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls, *args, **kwargs)
            cls._instance.__client = None
        return cls._instance
    
    def __init__(self, database='test', repo_collection='repos', embeddings_collection='embeddings'):
        # Set up basic logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Load environment variables
        password = os.environ.get("MONGOPASSWORD")

        # Initialize client (or use local files if a connection to MongoDB can't be made)
        self.USE_MONGODB = False
        self.__initialize_database_client(password)
        self.__database = self.__client[database]
        self.__repos = self.__database[repo_collection]
        self.__embeddings = self.__database[embeddings_collection]

    def __initialize_database_client(self, password):
        if self.__client is not None:
            return
        
        client = None
        connection_string = (
                f"mongodb+srv://samarkaranch:{password}@cluster0.269ml.mongodb.net/"
                "?retryWrites=true&w=majority&appName=Cluster0"
            )
        
        try:
            client = MongoClient(connection_string)
            self.logger.info("Connected to MongoDB successfully.")
            self.USE_MONGODB = True
        except ConnectionFailure as e:
            self.logger.error(f"Could not connect to MongoDB: {e}")
        
        self.__client = client
    
    def get_repo_collection(self):
        """
        Gets the reference to the repository collection on MongoDB.

        :return: The repository collection.
        """
        return self.__repos
    
    def get_embeddings_collection(self):
        """
        Gets the reference to the embeddings collection on MongoDB.

        :return: The embeddings collection.
        """
        return self.__embeddings