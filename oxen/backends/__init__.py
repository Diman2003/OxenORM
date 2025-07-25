"""
OxenORM Database Backends

This package provides database-specific backends for OxenORM, including:
- SQLite backend
- MySQL backend  
- PostgreSQL backend
- Database-specific optimizations
- Connection pooling
- Query optimization
"""

from .base import BaseBackend, ConnectionPool, DatabaseConfig
from .sqlite import SQLiteBackend
from .mysql import MySQLBackend
from .postgresql import PostgreSQLBackend

__all__ = [
    'BaseBackend',
    'ConnectionPool', 
    'DatabaseConfig',
    'SQLiteBackend',
    'MySQLBackend',
    'PostgreSQLBackend'
] 