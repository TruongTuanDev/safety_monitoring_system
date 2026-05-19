"""Authentication package for Safety Monitoring System.
Provides simple register/login helpers backed by MongoDB.
"""

from .manager import register_user, authenticate_user, ensure_indexes
from .db import DatabaseClient

__all__ = [
    'register_user',
    'authenticate_user',
    'ensure_indexes',
    'DatabaseClient',
]
