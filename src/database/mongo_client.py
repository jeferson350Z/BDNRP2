import motor.motor_asyncio as motor_async
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "transflow_db")

mongo_client = None
db = None
