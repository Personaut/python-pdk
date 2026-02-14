"""Storage interfaces for Personaut PDK.

This module provides storage interfaces and implementations for persisting
individuals, memories, and simulation data.

Example:
    >>> from personaut.interfaces import SQLiteStorage, FileStorage
    >>> storage = SQLiteStorage("personaut.db")
    >>> storage.save_individual({"name": "Alice", "individual_type": "simulated"})

Available implementations:
    - SQLiteStorage: Persistent SQLite database storage
    - FileStorage: File-based JSON storage for development
"""

from personaut.interfaces.file import FileStorage
from personaut.interfaces.sqlite import SQLiteStorage
from personaut.interfaces.storage import BaseStorage, Storage


__all__ = [
    "BaseStorage",
    "FileStorage",
    "SQLiteStorage",
    "Storage",
]
