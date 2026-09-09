"""
Sets up a MongoDB connection used as our NoSQL logging store.

Every API call that requires a student ID gets logged here as a document
containing the student ID, the endpoint called, the HTTP method, the
query parameters used, and a UTC timestamp.

Connection details are read from environment variables so the same code
works locally, with Atlas, or in any deployment, without hardcoding
credentials:

    MONGO_URI       Connection string (default: mongodb://localhost:27017)
    MONGO_DB_NAME   Database name to use (default: room_booking_api)

For MongoDB Atlas, the simplest approach is a `.env` file in the project
root (loaded automatically via python-dotenv), e.g.:

    MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
    MONGO_DB_NAME=room_booking_api

Never commit a `.env` file containing real credentials -- add it to
.gitignore before pushing this project anywhere.
"""

import os
from datetime import datetime, timezone
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv

load_dotenv()  # reads a .env file in the project root, if present

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "room_booking_api")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
call_logs = db["api_calls"]


def log_call(student_id: str, endpoint: str, method: str, query_params: dict) -> dict:
    """Insert a single call-log document into MongoDB and return it."""
    record = {
        "student_id": student_id,
        "endpoint": endpoint,
        "method": method,
        "query_params": query_params,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    call_logs.insert_one(record)
    record.pop("_id", None)  # drop Mongo's ObjectId, not JSON-serialisable by default
    return record


def _clean(doc: dict) -> dict:
    """Convert a MongoDB document to a plain JSON-serialisable dict."""
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc


def get_all_logs() -> list[dict]:
    """Return every logged call, most recent first."""
    cursor = call_logs.find().sort("timestamp", DESCENDING)
    return [_clean(doc) for doc in cursor]


def get_logs_for_student(student_id: str) -> list[dict]:
    """Return every logged call made using a specific student ID."""
    cursor = call_logs.find({"student_id": student_id}).sort("timestamp", DESCENDING)
    return [_clean(doc) for doc in cursor]
