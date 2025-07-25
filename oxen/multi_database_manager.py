#!/usr/bin/env python3
"""
Multi-Database Manager for OxenORM

This module provides a unified interface for managing multiple database backends,
including database switching, connection pooling, and database-specific optimizations.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from urllib.parse import urlparse
from contextlib import asynccontextmanager

from .backends.base import BaseBackend, DatabaseConfig
from .backends.sqlite import SQLiteBackend
from .backends.mysql import MySQLBackend
from .backends.postgresql import PostgreSQLBackend

logger = logging.getLogger(__name__)


@dataclass
class DatabaseInfo:
    """Information about a database connection."""
    name: str
    backend: BaseBackend
    config: DatabaseConfig
    is_primary: bool = False
    is_read_only: bool = False


class MultiDatabaseManager:
    """Manager for multiple database backends."""
    
    def __init__(self):
        self.databases: Dict[str, DatabaseInfo] = {}
        self.primary_database: Optional[str] = None
        self._initialized = False
        self._lock = asyncio.Lock()
    
    def add_database(
        self,
        name: str,
        url: str,
        is_primary: bool = False,
        is_read_only: bool = False,
        **config_options
    ) -> str:
        """
        Add a database to the manager.
        
        Args:
            name: Unique name for the database
            url: Database connection URL
            is_primary: Whether this is the primary database
            is_read_only: Whether this database is read-only
            **config_options: Additional configuration options
        
        Returns:
            Database name
        """
        if name in self.databases:
            raise ValueError(f"Database '{name}' already exists")
        
        # Parse URL and create config
        config = self._parse_url(url, **config_options)
        backend = self._create_backend(config)
        
        # Create database info
        db_info = DatabaseInfo(
            name=name,
            backend=backend,
            config=config,
            is_primary=is_primary,
            is_read_only=is_read_only
        )
        
        self.databases[name] = db_info
        
        # Set as primary if specified
        if is_primary:
            self.primary_database = name
        
        # Set as primary if it's the first database
        if not self.primary_database:
            self.primary_database = name
        
        logger.info(f"Added database '{name}' ({backend.get_dialect()})")
        return name
    
    def _parse_url(self, url: str, **config_options) -> DatabaseConfig:
        """Parse a database URL and create configuration."""
        parsed = urlparse(url)
        
        # Extract basic connection info
        config = DatabaseConfig(
            host=parsed.hostname or "localhost",
            port=parsed.port or self._get_default_port(parsed.scheme),
            username=parsed.username or "",
            password=parsed.password or "",
            database=parsed.path.lstrip("/") if parsed.path else "",
            **config_options
        )
        
        # Set database-specific options
        if parsed.scheme == "sqlite":
            config.sqlite_path = parsed.path or ":memory:"
        elif parsed.scheme == "mysql":
            config.port = config.port or 3306
        elif parsed.scheme == "postgresql":
            config.port = config.port or 5432
        
        return config
    
    def _get_default_port(self, scheme: str) -> int:
        """Get default port for database scheme."""
        defaults = {
            "sqlite": 0,  # SQLite doesn't use ports
            "mysql": 3306,
            "postgresql": 5432,
            "postgres": 5432
        }
        return defaults.get(scheme, 3306)
    
    def _create_backend(self, config: DatabaseConfig) -> BaseBackend:
        """Create appropriate backend based on configuration."""
        # Determine backend type from connection string
        conn_str = config.get_connection_string() if hasattr(config, 'get_connection_string') else ""
        
        if "sqlite" in conn_str or config.sqlite_path:
            return SQLiteBackend(config)
        elif "mysql" in conn_str or config.port == 3306:
            return MySQLBackend(config)
        elif "postgresql" in conn_str or config.port == 5432:
            return PostgreSQLBackend(config)
        else:
            # Default to SQLite
            return SQLiteBackend(config)
    
    async def initialize(self):
        """Initialize all database backends."""
        if self._initialized:
            return
        
        async with self._lock:
            for name, db_info in self.databases.items():
                try:
                    await db_info.backend.initialize()
                    logger.info(f"Initialized database '{name}'")
                except Exception as e:
                    logger.error(f"Failed to initialize database '{name}': {e}")
                    raise
        
        self._initialized = True
        logger.info(f"Initialized {len(self.databases)} databases")
    
    async def close(self):
        """Close all database connections."""
        async with self._lock:
            for name, db_info in self.databases.items():
                try:
                    await db_info.backend.close()
                    logger.info(f"Closed database '{name}'")
                except Exception as e:
                    logger.error(f"Failed to close database '{name}': {e}")
        
        self._initialized = False
        logger.info("Closed all database connections")
    
    def get_database(self, name: Optional[str] = None) -> DatabaseInfo:
        """Get database info by name or primary database."""
        if name is None:
            name = self.primary_database
        
        if name not in self.databases:
            raise ValueError(f"Database '{name}' not found")
        
        return self.databases[name]
    
    def get_backend(self, name: Optional[str] = None) -> BaseBackend:
        """Get backend by name or primary database."""
        return self.get_database(name).backend
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """List all databases with their information."""
        databases = []
        for name, db_info in self.databases.items():
            databases.append({
                'name': name,
                'dialect': db_info.backend.get_dialect(),
                'is_primary': db_info.is_primary,
                'is_read_only': db_info.is_read_only,
                'connection_string': db_info.backend.get_connection_string(),
                'features': db_info.backend.get_supported_features()
            })
        return databases
    
    async def execute_on_database(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        database_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query on a specific database."""
        backend = self.get_backend(database_name)
        return await backend.execute(sql, params)
    
    async def execute_on_all_databases(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        exclude_read_only: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute a query on all databases."""
        results = {}
        
        for name, db_info in self.databases.items():
            if exclude_read_only and db_info.is_read_only:
                continue
            
            try:
                result = await db_info.backend.execute(sql, params)
                results[name] = result
            except Exception as e:
                logger.error(f"Failed to execute on database '{name}': {e}")
                results[name] = []
        
        return results
    
    async def execute_on_read_replicas(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute a query on read replicas."""
        results = {}
        
        for name, db_info in self.databases.items():
            if db_info.is_read_only:
                try:
                    result = await db_info.backend.execute(sql, params)
                    results[name] = result
                except Exception as e:
                    logger.error(f"Failed to execute on read replica '{name}': {e}")
                    results[name] = []
        
        return results
    
    @asynccontextmanager
    async def transaction(self, database_name: Optional[str] = None):
        """Get a transaction context for a specific database."""
        backend = self.get_backend(database_name)
        async with backend.transaction() as conn:
            yield conn
    
    @asynccontextmanager
    async def connection(self, database_name: Optional[str] = None):
        """Get a connection for a specific database."""
        backend = self.get_backend(database_name)
        async with backend.get_connection() as conn:
            yield conn
    
    def switch_primary(self, database_name: str):
        """Switch the primary database."""
        if database_name not in self.databases:
            raise ValueError(f"Database '{database_name}' not found")
        
        # Update primary flags
        for name, db_info in self.databases.items():
            db_info.is_primary = (name == database_name)
        
        self.primary_database = database_name
        logger.info(f"Switched primary database to '{database_name}'")
    
    def add_read_replica(self, name: str, url: str, **config_options):
        """Add a read replica database."""
        return self.add_database(name, url, is_primary=False, is_read_only=True, **config_options)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics for all databases."""
        stats = {}
        
        for name, db_info in self.databases.items():
            try:
                pool_stats = db_info.backend.get_pool_stats()
                perf_stats = db_info.backend.get_performance_stats()
                
                stats[name] = {
                    'dialect': db_info.backend.get_dialect(),
                    'is_primary': db_info.is_primary,
                    'is_read_only': db_info.is_read_only,
                    'pool_stats': pool_stats,
                    'performance_stats': perf_stats
                }
            except Exception as e:
                logger.error(f"Failed to get stats for database '{name}': {e}")
                stats[name] = {'error': str(e)}
        
        return stats
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all databases."""
        health = {}
        
        for name, db_info in self.databases.items():
            try:
                # Try to execute a simple query
                await db_info.backend.execute("SELECT 1")
                health[name] = True
            except Exception as e:
                logger.error(f"Health check failed for database '{name}': {e}")
                health[name] = False
        
        return health
    
    async def backup_database(self, database_name: str, backup_path: str):
        """Backup a database."""
        db_info = self.get_database(database_name)
        backend = db_info.backend
        
        if isinstance(backend, SQLiteBackend):
            # SQLite backup
            import shutil
            shutil.copy2(db_info.config.sqlite_path, backup_path)
        elif isinstance(backend, MySQLBackend):
            # MySQL backup using mysqldump
            import subprocess
            cmd = [
                'mysqldump',
                f'--host={db_info.config.host}',
                f'--port={db_info.config.port}',
                f'--user={db_info.config.username}',
                f'--password={db_info.config.password}',
                db_info.config.database
            ]
            with open(backup_path, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
        elif isinstance(backend, PostgreSQLBackend):
            # PostgreSQL backup using pg_dump
            import subprocess
            cmd = [
                'pg_dump',
                f'--host={db_info.config.host}',
                f'--port={db_info.config.port}',
                f'--username={db_info.config.username}',
                f'--dbname={db_info.config.database}',
                '--no-password'
            ]
            with open(backup_path, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
        
        logger.info(f"Backed up database '{database_name}' to {backup_path}")
    
    def get_optimal_database(self, operation: str = "read") -> str:
        """Get the optimal database for an operation."""
        if operation == "read":
            # Prefer read replicas for read operations
            for name, db_info in self.databases.items():
                if db_info.is_read_only:
                    return name
        
        # Default to primary database
        return self.primary_database


# Global multi-database manager instance
_global_manager = None


def get_multi_database_manager() -> MultiDatabaseManager:
    """Get the global multi-database manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = MultiDatabaseManager()
    return _global_manager


async def initialize_databases(*database_configs):
    """Initialize multiple databases from configuration."""
    manager = get_multi_database_manager()
    
    for config in database_configs:
        manager.add_database(**config)
    
    await manager.initialize()
    return manager 