"""
MongoDB connection and configuration
"""
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import logging

logger = logging.getLogger(__name__)

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGO_DB_NAME", "smart_file_organizer")

# Global client (lazy initialization)
_client = None
_db = None

def get_mongo_client():
    """Get or create MongoDB client"""
    global _client
    if _client is None:
        try:
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            _client.admin.command('ping')
            logger.info("Connected to MongoDB")
        except ServerSelectionTimeoutError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            _client = None
    return _client

def get_database():
    """Get MongoDB database"""
    global _db
    if _db is None:
        client = get_mongo_client()
        if client is not None:
            _db = client[DATABASE_NAME]
    return _db

def get_file_movements_collection():
    """Get file movements collection"""
    db = get_database()
    if db is not None:
        collection = db["file_movements"]
        # Create index for faster queries
        collection.create_index("timestamp")
        collection.create_index("original_path")
        collection.create_index("new_path")
        return collection
    return None

def close_mongo_connection():
    """Close MongoDB connection"""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("Closed MongoDB connection")
