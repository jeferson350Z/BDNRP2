from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "transflow")

mongo_client = MongoClient(MONGO_URL)
db = mongo_client[MONGO_DB_NAME]
