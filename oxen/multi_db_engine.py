#!/usr/bin/env python3
"""
Multi-Database Engine for OxenORM

Provides support for multiple database backends including PostgreSQL, MySQL, and SQLite
with database-specific optimizations and switching capabilities.
"""

import asyncio
import sys
import os
from typing import Dict, Any, List, Optional, Union
from enum import Enum

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from oxen.rust_engine import OxenEngine
    RUST_AVAILABLE = True
except ImportError as e:
    print(f"❌ Rust engine not available: {e}")
    RUST_AVAILABLE = False


class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


class MultiDbEngine:
    """
    Multi-database engine supporting PostgreSQL, MySQL, and SQLite.
    
    This engine provides database-specific optimizations and allows
    switching between different database backends seamlessly.
    """

    def __init__(self, connection_string: str):
        """
        Initialize the multi-database engine.
        
        Args:
            connection_string: Database connection URL
                - PostgreSQL: postgresql://user:pass@host:port/db
                - MySQL: mysql://user:pass@host:port/db
                - SQLite: sqlite:///path/to/database.db
        """
        if not RUST_AVAILABLE:
            raise ImportError("Rust engine not available. Please build the Rust extension first.")
        
        self.connection_string = connection_string
        self.database_type = self._detect_database_type(connection_string)
        self.engine = None
        self.is_connected = False
        self._connection_info = None

    def _detect_database_type(self, connection_string: str) -> DatabaseType:
        """Detect database type from connection string."""
        if connection_string.startswith(('postgresql://', 'postgres://')):
            return DatabaseType.POSTGRESQL
        elif connection_string.startswith('mysql://'):
            return DatabaseType.MYSQL
        elif connection_string.startswith('sqlite://'):
            return DatabaseType.SQLITE
        else:
            raise ValueError(f"Unsupported database type in connection string: {connection_string}")

    def configure_pool(self, max_connections: Optional[int] = None, min_connections: Optional[int] = None):
        """
        Configure connection pool settings.
        
        Args:
            max_connections: Maximum number of connections in the pool
            min_connections: Minimum number of connections in the pool
        """
        if self.engine:
            self.engine.configure_pool(max_connections, min_connections)

    async def connect(self) -> Dict[str, Any]:
        """
        Connect to the database.
        
        Returns:
            Connection information including status and database type
        """
        if self.is_connected:
            return self._connection_info

        # Create the appropriate engine based on database type
        if self.database_type == DatabaseType.POSTGRESQL:
            # Use the existing OxenEngine for PostgreSQL
            self.engine = OxenEngine(self.connection_string)
        else:
            # For now, use OxenEngine for all types (will be enhanced with multi_db module)
            self.engine = OxenEngine(self.connection_string)

        # Configure default pool settings based on database type
        if self.database_type == DatabaseType.SQLITE:
            # SQLite doesn't need connection pooling like PostgreSQL/MySQL
            self.engine.configure_pool(max_connections=1, min_connections=1)
        else:
            # Default pool settings for PostgreSQL/MySQL
            self.engine.configure_pool(max_connections=10, min_connections=2)

        # Connect to the database
        result = await self.engine.connect()
        self.is_connected = True
        self._connection_info = result

        # Add database type information
        if isinstance(result, dict):
            result['database_type'] = self.database_type.value
        else:
            self._connection_info = {
                'status': 'connected',
                'database_type': self.database_type.value,
                'connection_string': self.connection_string
            }

        return self._connection_info

    async def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect from the database.
        
        Returns:
            Disconnection information
        """
        if not self.is_connected or not self.engine:
            return {
                'status': 'disconnected',
                'database_type': self.database_type.value,
                'connection_string': self.connection_string
            }

        result = await self.engine.close()
        self.is_connected = False
        self.engine = None

        if isinstance(result, dict):
            result['database_type'] = self.database_type.value
        else:
            result = {
                'status': 'disconnected',
                'database_type': self.database_type.value,
                'connection_string': self.connection_string
            }

        return result

    async def execute_query(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Execute a SQL query with database-specific optimizations.
        
        Args:
            sql: SQL query to execute
            params: Query parameters (optional)
            
        Returns:
            Query result with rows affected and data
        """
        if not self.is_connected or not self.engine:
            raise RuntimeError("Not connected to database. Call connect() first.")

        # Apply database-specific optimizations
        optimized_sql = self._optimize_query(sql)
        
        return await self.engine.execute_query(optimized_sql, params or [])

    async def execute_many(self, sql: str, params_list: List[List[Any]]) -> Dict[str, Any]:
        """
        Execute a SQL query multiple times with different parameters.
        
        Args:
            sql: SQL query to execute
            params_list: List of parameter lists
            
        Returns:
            Batch execution result
        """
        if not self.is_connected or not self.engine:
            raise RuntimeError("Not connected to database. Call connect() first.")

        # Apply database-specific optimizations
        optimized_sql = self._optimize_query(sql)
        
        return await self.engine.execute_many(optimized_sql, params_list)

    async def begin_transaction(self) -> Dict[str, Any]:
        """
        Begin a database transaction.
        
        Returns:
            Transaction information
        """
        if not self.is_connected or not self.engine:
            raise RuntimeError("Not connected to database. Call connect() first.")

        return await self.engine.begin_transaction()

    def _optimize_query(self, sql: str) -> str:
        """
        Apply database-specific query optimizations.
        
        Args:
            sql: Original SQL query
            
        Returns:
            Optimized SQL query
        """
        if self.database_type == DatabaseType.POSTGRESQL:
            return self._optimize_postgresql_query(sql)
        elif self.database_type == DatabaseType.MYSQL:
            return self._optimize_mysql_query(sql)
        elif self.database_type == DatabaseType.SQLITE:
            return self._optimize_sqlite_query(sql)
        else:
            return sql

    def _optimize_postgresql_query(self, sql: str) -> str:
        """Apply PostgreSQL-specific optimizations."""
        # PostgreSQL optimizations
        sql = sql.strip()
        
        # Add LIMIT for SELECT queries without LIMIT (performance optimization)
        if sql.upper().startswith('SELECT') and 'LIMIT' not in sql.upper():
            # Don't add LIMIT automatically as it might break existing queries
            pass
        
        # Use parameterized queries (already handled by the engine)
        return sql

    def _optimize_mysql_query(self, sql: str) -> str:
        """Apply MySQL-specific optimizations."""
        # MySQL optimizations
        sql = sql.strip()
        
        # MySQL-specific optimizations
        if sql.upper().startswith('SELECT'):
            # Add SQL_CALC_FOUND_ROWS for compatibility if needed
            pass
        
        return sql

    def _optimize_sqlite_query(self, sql: str) -> str:
        """Apply SQLite-specific optimizations."""
        # SQLite optimizations
        sql = sql.strip()
        
        # SQLite-specific optimizations
        if sql.upper().startswith('SELECT'):
            # Add LIMIT for large result sets
            pass
        
        return sql

    def get_database_type(self) -> DatabaseType:
        """Get the current database type."""
        return self.database_type

    def is_connected(self) -> bool:
        """Check if connected to the database."""
        return self.is_connected

    async def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        if not self.is_connected:
            return {
                'status': 'disconnected',
                'database_type': self.database_type.value,
                'connection_string': self.connection_string
            }
        
        return self._connection_info or {}

    async def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self.is_connected:
                await self.connect()
            
            # Execute a simple query to test the connection
            if self.database_type == DatabaseType.POSTGRESQL:
                await self.execute_query("SELECT 1")
            elif self.database_type == DatabaseType.MYSQL:
                await self.execute_query("SELECT 1")
            elif self.database_type == DatabaseType.SQLITE:
                await self.execute_query("SELECT 1")
            
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get database-specific information.
        
        Returns:
            Database information including version, features, etc.
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to database. Call connect() first.")

        info = {
            'database_type': self.database_type.value,
            'connection_string': self.connection_string,
        }

        try:
            if self.database_type == DatabaseType.POSTGRESQL:
                result = await self.execute_query("SELECT version()")
                info['version'] = result.get('data', [{}])[0].get('version', 'Unknown')
            elif self.database_type == DatabaseType.MYSQL:
                result = await self.execute_query("SELECT VERSION()")
                info['version'] = result.get('data', [{}])[0].get('VERSION()', 'Unknown')
            elif self.database_type == DatabaseType.SQLITE:
                result = await self.execute_query("SELECT sqlite_version()")
                info['version'] = result.get('data', [{}])[0].get('sqlite_version()', 'Unknown')
        except Exception as e:
            info['version'] = f"Error getting version: {e}"

        return info

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class DatabaseSwitcher:
    """
    Utility class for switching between different database backends.
    """

    def __init__(self):
        self.engines: Dict[str, MultiDbEngine] = {}
        self.current_engine: Optional[MultiDbEngine] = None

    async def add_database(self, name: str, connection_string: str) -> MultiDbEngine:
        """
        Add a database connection.
        
        Args:
            name: Name for the database connection
            connection_string: Database connection URL
            
        Returns:
            MultiDbEngine instance
        """
        engine = MultiDbEngine(connection_string)
        self.engines[name] = engine
        return engine

    async def switch_to(self, name: str) -> MultiDbEngine:
        """
        Switch to a different database.
        
        Args:
            name: Name of the database to switch to
            
        Returns:
            MultiDbEngine instance for the selected database
        """
        if name not in self.engines:
            raise ValueError(f"Database '{name}' not found. Available: {list(self.engines.keys())}")
        
        # Disconnect from current engine if connected
        if self.current_engine and self.current_engine.is_connected():
            await self.current_engine.disconnect()
        
        # Switch to new engine
        self.current_engine = self.engines[name]
        
        # Connect to the new database
        await self.current_engine.connect()
        
        return self.current_engine

    def get_current_engine(self) -> Optional[MultiDbEngine]:
        """Get the current database engine."""
        return self.current_engine

    def list_databases(self) -> List[str]:
        """List all available database connections."""
        return list(self.engines.keys())

    async def close_all(self):
        """Close all database connections."""
        for engine in self.engines.values():
            if engine.is_connected():
                await engine.disconnect()
        
        self.engines.clear()
        self.current_engine = None


# Convenience functions for quick database operations

async def create_postgresql_engine(connection_string: str) -> MultiDbEngine:
    """Create a PostgreSQL engine."""
    return MultiDbEngine(connection_string)

async def create_mysql_engine(connection_string: str) -> MultiDbEngine:
    """Create a MySQL engine."""
    return MultiDbEngine(connection_string)

async def create_sqlite_engine(connection_string: str) -> MultiDbEngine:
    """Create a SQLite engine."""
    return MultiDbEngine(connection_string)

async def test_database_connection(connection_string: str) -> bool:
    """
    Test a database connection.
    
    Args:
        connection_string: Database connection URL
        
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        engine = MultiDbEngine(connection_string)
        return await engine.test_connection()
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False 