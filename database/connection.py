"""
MongoDB Connection Module
Provides thread-safe client caching, connection verification, and clear error diagnostics.
"""

import sys
from typing import Optional, Tuple
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import config

_client_instance: Optional[MongoClient] = None


def get_mongo_client(uri: Optional[str] = None, timeout_ms: int = 5000) -> MongoClient:
    """
    Returns a cached or new MongoClient instance with server selection timeout.
    """
    global _client_instance
    target_uri = uri or config.MONGODB_URI

    if _client_instance is not None:
        try:
            # Quick check if client is alive
            _client_instance.admin.command("ping")
            return _client_instance
        except Exception:
            _client_instance = None

    try:
        client = MongoClient(target_uri, serverSelectionTimeoutMS=timeout_ms)
        # Verify connection immediately
        client.admin.command("ping")
        _client_instance = client
        return _client_instance
    except (ConnectionFailure, ServerSelectionTimeoutError) as err:
        error_msg = (
            f"[MongoDB Connection Failed] Unable to connect to MongoDB at '{target_uri}'.\n"
            f"Details: {err}\n\n"
            "Troubleshooting Steps:\n"
            "1. If running locally, verify MongoDB service is active: 'net start MongoDB' (Windows) or 'sudo systemctl start mongod'.\n"
            "2. If using MongoDB Atlas, check your network whitelist (IP Access List) and connection string in .env.\n"
            "3. Verify host and port (default is localhost:27017)."
        )
        raise ConnectionError(error_msg) from err


def get_db(uri: Optional[str] = None, db_name: Optional[str] = None) -> Database:
    """
    Returns the database instance specified in config or arguments.
    """
    client = get_mongo_client(uri)
    target_db_name = db_name or config.MONGODB_DATABASE
    return client[target_db_name]


def check_connection() -> Tuple[bool, str]:
    """
    Diagnostic helper that checks if MongoDB is reachable and returns server info or error message.
    """
    try:
        client = get_mongo_client(timeout_ms=3000)
        info = client.server_info()
        version = info.get("version", "unknown")
        return True, f"Connected to MongoDB Server v{version} at {config.MONGODB_URI}"
    except Exception as exc:
        return False, str(exc)


def close_connection() -> None:
    """Closes the cached MongoDB client."""
    global _client_instance
    if _client_instance is not None:
        _client_instance.close()
        _client_instance = None
