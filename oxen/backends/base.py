#!/usr/bin/env python3
"""
Base Database Backend

This module defines the base interface for all database backends in OxenORM,
including connection pooling, query optimization, and database-specific features.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    host: str = "localhost"
    port: int = 3306
    database: str = ""
    username: str = ""
    password: str = ""
    charset: str = "utf8mb4"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    ssl_mode: str = "prefer"
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30
    
    # Database-specific options
    sqlite_path: str = ":memory:"
    mysql_autocommit: bool = True
    postgres_schema: str = "public"
    
    def __post_init__(self):
        """Validate configuration."""
        if self.pool_size < 1:
            raise ValueError("pool_size must be at least 1")
        if self.max_overflow < 0:
            raise ValueError("max_overflow must be non-negative")
        if self.pool_timeout < 0:
            raise ValueError("pool_timeout must be non-negative")


class ConnectionPool:
    """Connection pool for database connections."""
    
    def __init__(self, config: DatabaseConfig, backend: 'BaseBackend'):
        self.config = config
        self.backend = backend
        self.pool_size = config.pool_size
        self.max_overflow = config.max_overflow
        self.pool_timeout = config.pool_timeout
        self.pool_recycle = config.pool_recycle
        
        # Pool state
        self._pool: List[Any] = []
        self._in_use: List[Any] = []
        self._lock = asyncio.Lock()
        self._created_at = time.time()
        
        # Statistics
        self._total_connections = 0
        self._total_acquires = 0
        self._total_releases = 0
        self._failed_acquires = 0
    
    async def initialize(self):
        """Initialize the connection pool."""
        async with self._lock:
            # Create initial connections
            for _ in range(self.pool_size):
                try:
                    conn = await self.backend.create_connection(self.config)
                    self._pool.append(conn)
                    self._total_connections += 1
                except Exception as e:
                    logger.error(f"Failed to create initial connection: {e}")
                    raise
    
    async def acquire(self) -> Any:
        """Acquire a connection from the pool."""
        start_time = time.time()
        self._total_acquires += 1
        
        async with self._lock:
            # Try to get from pool
            if self._pool:
                conn = self._pool.pop()
                self._in_use.append(conn)
                return conn
            
            # Try to create new connection if under max_overflow
            if len(self._in_use) < self.pool_size + self.max_overflow:
                try:
                    conn = await self.backend.create_connection(self.config)
                    self._in_use.append(conn)
                    self._total_connections += 1
                    return conn
                except Exception as e:
                    logger.error(f"Failed to create new connection: {e}")
                    self._failed_acquires += 1
                    raise
            
            # Wait for connection to become available
            timeout = self.pool_timeout - (time.time() - start_time)
            if timeout <= 0:
                self._failed_acquires += 1
                raise TimeoutError("Connection pool timeout")
            
            # Wait for connection
            while not self._pool and timeout > 0:
                await asyncio.sleep(0.1)
                timeout -= 0.1
            
            if self._pool:
                conn = self._pool.pop()
                self._in_use.append(conn)
                return conn
            else:
                self._failed_acquires += 1
                raise TimeoutError("Connection pool timeout")
    
    async def release(self, conn: Any):
        """Release a connection back to the pool."""
        self._total_releases += 1
        
        async with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                
                # Check if connection is still valid
                if await self.backend.is_connection_valid(conn):
                    # Check if connection needs recycling
                    if time.time() - self._created_at > self.pool_recycle:
                        await self.backend.close_connection(conn)
                        self._total_connections -= 1
                    else:
                        self._pool.append(conn)
                else:
                    # Connection is invalid, close it
                    await self.backend.close_connection(conn)
                    self._total_connections -= 1
    
    async def close(self):
        """Close all connections in the pool."""
        async with self._lock:
            # Close all connections
            for conn in self._pool + self._in_use:
                await self.backend.close_connection(conn)
            
            self._pool.clear()
            self._in_use.clear()
            self._total_connections = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'total_connections': self._total_connections,
            'available_connections': len(self._pool),
            'in_use_connections': len(self._in_use),
            'total_acquires': self._total_acquires,
            'total_releases': self._total_releases,
            'failed_acquires': self._failed_acquires,
            'utilization': len(self._in_use) / max(self._total_connections, 1)
        }


class BaseBackend(ABC):
    """Base class for all database backends."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = ConnectionPool(config, self)
        self._initialized = False
    
    @abstractmethod
    async def create_connection(self, config: DatabaseConfig) -> Any:
        """Create a new database connection."""
        pass
    
    @abstractmethod
    async def close_connection(self, conn: Any):
        """Close a database connection."""
        pass
    
    @abstractmethod
    async def is_connection_valid(self, conn: Any) -> bool:
        """Check if a connection is still valid."""
        pass
    
    @abstractmethod
    async def execute_query(self, conn: Any, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        pass
    
    @abstractmethod
    async def execute_many(self, conn: Any, sql: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute multiple queries with different parameters."""
        pass
    
    @abstractmethod
    async def begin_transaction(self, conn: Any):
        """Begin a transaction."""
        pass
    
    @abstractmethod
    async def commit_transaction(self, conn: Any):
        """Commit a transaction."""
        pass
    
    @abstractmethod
    async def rollback_transaction(self, conn: Any):
        """Rollback a transaction."""
        pass
    
    @abstractmethod
    def get_connection_string(self) -> str:
        """Get the connection string for this backend."""
        pass
    
    @abstractmethod
    def get_dialect(self) -> str:
        """Get the SQL dialect for this backend."""
        pass
    
    async def initialize(self):
        """Initialize the backend and connection pool."""
        if not self._initialized:
            await self.pool.initialize()
            self._initialized = True
    
    async def close(self):
        """Close the backend and all connections."""
        await self.pool.close()
        self._initialized = False
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)
    
    @asynccontextmanager
    async def transaction(self):
        """Get a connection with transaction support."""
        async with self.get_connection() as conn:
            await self.begin_transaction(conn)
            try:
                yield conn
                await self.commit_transaction(conn)
            except Exception:
                await self.rollback_transaction(conn)
                raise
    
    async def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query using a connection from the pool."""
        async with self.get_connection() as conn:
            return await self.execute_query(conn, sql, params)
    
    async def execute_many_queries(self, sql: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute multiple queries using a connection from the pool."""
        async with self.get_connection() as conn:
            return await self.execute_many(conn, sql, params_list)
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return self.pool.get_stats()
    
    def supports_feature(self, feature: str) -> bool:
        """Check if the backend supports a specific feature."""
        return feature in self.get_supported_features()
    
    @abstractmethod
    def get_supported_features(self) -> List[str]:
        """Get list of supported features for this backend."""
        pass
    
    def optimize_query(self, sql: str) -> str:
        """Optimize a query for this backend."""
        # Default implementation - subclasses can override
        return sql
    
    def get_parameter_style(self) -> str:
        """Get the parameter style for this backend."""
        return "named"  # Default to named parameters
    
    def escape_identifier(self, identifier: str) -> str:
        """Escape an identifier for this backend."""
        # Default implementation - subclasses can override
        return f'"{identifier}"'
    
    def get_auto_increment_sql(self) -> str:
        """Get the auto-increment SQL for this backend."""
        # Default implementation - subclasses can override
        return "AUTO_INCREMENT" 