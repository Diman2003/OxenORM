#!/usr/bin/env python3
"""
SQLite Backend for OxenORM

This module provides SQLite-specific backend implementation with:
- Connection pooling
- Query optimization
- SQLite-specific features
- Performance optimizations
"""

import aiosqlite
import asyncio
import logging
from typing import Dict, List, Any, Optional
from .base import BaseBackend, DatabaseConfig

logger = logging.getLogger(__name__)


class SQLiteBackend(BaseBackend):
    """SQLite backend implementation."""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.db_path = config.sqlite_path
        self._connections = set()
    
    async def create_connection(self, config: DatabaseConfig) -> aiosqlite.Connection:
        """Create a new SQLite connection."""
        try:
            conn = await aiosqlite.connect(
                self.db_path,
                timeout=config.connect_timeout,
                check_same_thread=False,
                isolation_level=None  # Enable autocommit mode
            )
            
            # Configure connection
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute("PRAGMA journal_mode = WAL")
            await conn.execute("PRAGMA synchronous = NORMAL")
            await conn.execute("PRAGMA cache_size = 10000")
            await conn.execute("PRAGMA temp_store = MEMORY")
            
            # Enable row factory for dict results
            conn.row_factory = aiosqlite.Row
            
            self._connections.add(conn)
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create SQLite connection: {e}")
            raise
    
    async def close_connection(self, conn: aiosqlite.Connection):
        """Close a SQLite connection."""
        try:
            if conn in self._connections:
                self._connections.remove(conn)
            await conn.close()
        except Exception as e:
            logger.error(f"Failed to close SQLite connection: {e}")
    
    async def is_connection_valid(self, conn: aiosqlite.Connection) -> bool:
        """Check if a SQLite connection is still valid."""
        try:
            await conn.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    async def execute_query(self, conn: aiosqlite.Connection, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        try:
            # Optimize query for SQLite
            optimized_sql = self.optimize_query(sql)
            
            if params:
                cursor = await conn.execute(optimized_sql, params)
            else:
                cursor = await conn.execute(optimized_sql)
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to execute SQLite query: {e}")
            logger.error(f"SQL: {sql}")
            logger.error(f"Params: {params}")
            raise
    
    async def execute_many(self, conn: aiosqlite.Connection, sql: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute multiple queries with different parameters."""
        try:
            # Optimize query for SQLite
            optimized_sql = self.optimize_query(sql)
            
            cursor = await conn.executemany(optimized_sql, params_list)
            return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Failed to execute many SQLite queries: {e}")
            logger.error(f"SQL: {sql}")
            raise
    
    async def begin_transaction(self, conn: aiosqlite.Connection):
        """Begin a transaction."""
        await conn.execute("BEGIN TRANSACTION")
    
    async def commit_transaction(self, conn: aiosqlite.Connection):
        """Commit a transaction."""
        await conn.commit()
    
    async def rollback_transaction(self, conn: aiosqlite.Connection):
        """Rollback a transaction."""
        await conn.rollback()
    
    def get_connection_string(self) -> str:
        """Get the SQLite connection string."""
        return f"sqlite:///{self.db_path}"
    
    def get_dialect(self) -> str:
        """Get the SQL dialect for SQLite."""
        return "sqlite"
    
    def get_supported_features(self) -> List[str]:
        """Get list of supported features for SQLite."""
        return [
            "transactions",
            "foreign_keys",
            "indexes",
            "views",
            "triggers",
            "full_text_search",
            "json_functions",
            "window_functions",
            "common_table_expressions",
            "recursive_queries"
        ]
    
    def optimize_query(self, sql: str) -> str:
        """Optimize a query for SQLite."""
        # SQLite-specific optimizations
        optimized = sql
        
        # Add EXPLAIN QUERY PLAN for debugging
        if self.config.echo:
            optimized = f"EXPLAIN QUERY PLAN {optimized}"
        
        # Optimize LIMIT clauses
        if "LIMIT" in optimized.upper():
            # Ensure LIMIT is properly placed
            pass
        
        # Optimize ORDER BY with LIMIT
        if "ORDER BY" in optimized.upper() and "LIMIT" in optimized.upper():
            # SQLite can optimize ORDER BY + LIMIT
            pass
        
        return optimized
    
    def get_parameter_style(self) -> str:
        """Get the parameter style for SQLite."""
        return "named"
    
    def escape_identifier(self, identifier: str) -> str:
        """Escape an identifier for SQLite."""
        return f'"{identifier}"'
    
    def get_auto_increment_sql(self) -> str:
        """Get the auto-increment SQL for SQLite."""
        return "AUTOINCREMENT"
    
    async def create_table(self, table_name: str, columns: List[Dict[str, Any]]):
        """Create a table with SQLite-specific optimizations."""
        column_defs = []
        for column in columns:
            name = column['name']
            type_name = column['type']
            nullable = column.get('nullable', True)
            primary_key = column.get('primary_key', False)
            auto_increment = column.get('auto_increment', False)
            
            # Build column definition
            col_def = f'"{name}" {type_name}'
            
            if not nullable:
                col_def += " NOT NULL"
            
            if primary_key:
                col_def += " PRIMARY KEY"
                if auto_increment:
                    col_def += " AUTOINCREMENT"
            
            column_defs.append(col_def)
        
        # Create table with SQLite optimizations
        sql = f"""
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {', '.join(column_defs)}
        )
        """
        
        async with self.get_connection() as conn:
            await self.execute_query(conn, sql)
            
            # Create indexes for better performance
            await self._create_default_indexes(conn, table_name, columns)
    
    async def _create_default_indexes(self, conn: aiosqlite.Connection, table_name: str, columns: List[Dict[str, Any]]):
        """Create default indexes for better performance."""
        for column in columns:
            if column.get('index', False):
                index_name = f"idx_{table_name}_{column['name']}"
                sql = f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table_name}" ("{column["name"]}")'
                await self.execute_query(conn, sql)
    
    async def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table information."""
        sql = f"PRAGMA table_info({self.escape_identifier(table_name)})"
        return await self.execute(sql)
    
    async def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a table."""
        sql = f"PRAGMA index_list({self.escape_identifier(table_name)})"
        return await self.execute(sql)
    
    async def analyze_table(self, table_name: str):
        """Analyze a table for better query planning."""
        sql = f"ANALYZE {self.escape_identifier(table_name)}"
        await self.execute(sql)
    
    async def vacuum(self):
        """Vacuum the database to reclaim space and optimize."""
        await self.execute("VACUUM")
    
    async def optimize(self):
        """Optimize the database."""
        await self.execute("PRAGMA optimize")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get SQLite performance statistics."""
        stats = self.get_pool_stats()
        
        # Add SQLite-specific stats
        stats.update({
            'database_path': self.db_path,
            'dialect': 'sqlite',
            'features': self.get_supported_features()
        })
        
        return stats 