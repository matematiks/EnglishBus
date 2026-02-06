"""
Database dependency for FastAPI
Provides SQLite connection via dependency injection
"""

import sqlite3
import os
from typing import Generator

# Database path relative to backend directory
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../englishbus.db")


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Dependency that provides database connection.
    
    Usage in endpoints:
    Dependency that provides a database connection.
    Ensures connection is properly closed after request.
    
    CRITICAL: check_same_thread=False required for FastAPI async
    """
    # Normalize path
    db_path = os.path.normpath(DATABASE_PATH)
    
    # Connect
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    
    try:
        yield conn
    finally:
        conn.close()
