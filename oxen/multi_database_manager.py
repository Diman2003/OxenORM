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

from .engine import create_engine, UnifiedEngine

logger = logging.getLogger(__name__)


@dataclass
class DatabaseInfo:
    """Information about a database connection (Rust-backed)."""
    name: str
    url: str
    engine: UnifiedEngine
    is_primary: bool = False
    is_read_only: bool = False


class MultiDatabaseManager:
    """Manager for multiple Rust-backed database engines."""
    
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
        
        # Create unified engine (Rust-backed)
        engine = create_engine(url, use_rust=True)
        
        # Create database info
        db_info = DatabaseInfo(
            name=name,
            url=url,
            engine=engine,
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
        
        logger.info(f"Added database '{name}' ({url.split(':', 1)[0]})")
        return name
    
    # Legacy URL parsing and backend creation removed; UnifiedEngine handles connection strings
    
    # Default port helper no longer used
    
    # Backend factory removed; using UnifiedEngine exclusively
    
    async def initialize(self):
        """Initialize all database backends."""
        if self._initialized:
            return
        
        async with self._lock:
            for name, db_info in self.databases.items():
                try:
                    await db_info.engine.connect()
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
                    await db_info.engine.disconnect()
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
    
    def get_backend(self, name: Optional[str] = None) -> UnifiedEngine:  # type: ignore
        """Return the Rust-backed engine for compatibility with old API name."""
        return self.get_database(name).engine
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """List all databases with their information."""
        databases = []
        for name, db_info in self.databases.items():
            databases.append({
                'name': name,
                'dialect': db_info.url.split(':', 1)[0],
                'is_primary': db_info.is_primary,
                'is_read_only': db_info.is_read_only,
                'connection_string': db_info.url,
                'features': []
            })
        return databases
    
    async def execute_on_database(
        self,
        sql: str,
        params: Optional[Union[Dict[str, Any], List[Any]]] = None,
        database_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query on a specific database."""
        db_info = self.get_database(database_name)
        # Convert params to positional list if dict provided
        param_list: Optional[List[Any]] = None
        if isinstance(params, dict):
            param_list = list(params.values())
        elif isinstance(params, list):
            param_list = params
        result = await db_info.engine.execute_query(sql, param_list)
        return result.get('data', [])
    
    async def execute_on_all_databases(
        self,
        sql: str,
        params: Optional[Union[Dict[str, Any], List[Any]]] = None,
        exclude_read_only: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute a query on all databases."""
        results = {}
        
        for name, db_info in self.databases.items():
            if exclude_read_only and db_info.is_read_only:
                continue
            
            try:
                param_list: Optional[List[Any]] = None
                if isinstance(params, dict):
                    param_list = list(params.values())
                elif isinstance(params, list):
                    param_list = params
                result = await db_info.engine.execute_query(sql, param_list)
                results[name] = result.get('data', [])
            except Exception as e:
                logger.error(f"Failed to execute on database '{name}': {e}")
                results[name] = []
        
        return results
    
    async def execute_on_read_replicas(
        self,
        sql: str,
        params: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute a query on read replicas."""
        results = {}
        
        for name, db_info in self.databases.items():
            if db_info.is_read_only:
                try:
                    param_list: Optional[List[Any]] = None
                    if isinstance(params, dict):
                        param_list = list(params.values())
                    elif isinstance(params, list):
                        param_list = params
                    result = await db_info.engine.execute_query(sql, param_list)
                    results[name] = result.get('data', [])
                except Exception as e:
                    logger.error(f"Failed to execute on read replica '{name}': {e}")
                    results[name] = []
        
        return results
    
    @asynccontextmanager
    async def transaction(self, database_name: Optional[str] = None):
        """Get a transaction context for a specific database."""
        db_info = self.get_database(database_name)
        async with db_info.engine.transaction():
            yield db_info.engine
    
    @asynccontextmanager
    async def connection(self, database_name: Optional[str] = None):
        """Get a connection for a specific database."""
        # UnifiedEngine does not expose raw DB connections; return engine for executing queries
        db_info = self.get_database(database_name)
        yield db_info.engine
    
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
        # Backup based on URL scheme
        from urllib.parse import urlparse
        import shutil
        parsed = urlparse(db_info.url)
        scheme = parsed.scheme
        if scheme == 'sqlite' and parsed.path and parsed.path not in (':memory:', ''):
            shutil.copy2(parsed.path, backup_path)
            logger.info(f"Backed up SQLite database '{database_name}' from {parsed.path} to {backup_path}")
        else:
            logger.warning("Backup for non-SQLite databases is not automated; use vendor tools (mysqldump/pg_dump).")
    
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