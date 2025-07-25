#!/usr/bin/env python3
"""
PostgreSQL Backend for OxenORM

This module provides PostgreSQL-specific backend implementation with:
- Connection pooling
- Query optimization
- PostgreSQL-specific features
- Performance optimizations
"""

import asyncpg
import asyncio
import logging
from typing import Dict, List, Any, Optional
from .base import BaseBackend, DatabaseConfig

logger = logging.getLogger(__name__)


class PostgreSQLBackend(BaseBackend):
    """PostgreSQL backend implementation."""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._connections = set()
    
    async def create_connection(self, config: DatabaseConfig) -> asyncpg.Connection:
        """Create a new PostgreSQL connection."""
        try:
            # Build connection parameters
            conn_params = {
                'host': config.host,
                'port': config.port,
                'user': config.username,
                'password': config.password,
                'database': config.database,
                'command_timeout': config.read_timeout,
                'server_settings': {
                    'application_name': 'oxenorm',
                    'timezone': 'UTC',
                    'client_encoding': 'UTF8',
                    'jit': 'off',  # Disable JIT for better performance in some cases
                    'random_page_cost': '1.1',  # Optimize for SSD
                    'effective_cache_size': '4GB',  # Assume 4GB cache
                    'work_mem': '4MB',  # Memory for query operations
                    'maintenance_work_mem': '64MB',  # Memory for maintenance
                    'shared_preload_libraries': 'pg_stat_statements',  # Enable query statistics
                }
            }
            
            # Add SSL configuration
            if config.ssl_mode != "disable":
                conn_params['ssl'] = 'require' if config.ssl_mode == "require" else True
            
            conn = await asyncpg.connect(**conn_params)
            
            # Configure connection for better performance
            await conn.execute("SET SESSION synchronous_commit = off")  # Faster commits
            await conn.execute("SET SESSION wal_buffers = 16MB")  # WAL buffer size
            await conn.execute("SET SESSION checkpoint_completion_target = 0.9")  # Checkpoint optimization
            
            # Enable query statistics if available
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
            except:
                # Extension might not be available
                pass
            
            self._connections.add(conn)
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection: {e}")
            raise
    
    async def close_connection(self, conn: asyncpg.Connection):
        """Close a PostgreSQL connection."""
        try:
            if conn in self._connections:
                self._connections.remove(conn)
            await conn.close()
        except Exception as e:
            logger.error(f"Failed to close PostgreSQL connection: {e}")
    
    async def is_connection_valid(self, conn: asyncpg.Connection) -> bool:
        """Check if a PostgreSQL connection is still valid."""
        try:
            await conn.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    async def execute_query(self, conn: asyncpg.Connection, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        try:
            # Optimize query for PostgreSQL
            optimized_sql = self.optimize_query(sql)
            
            if params:
                # Convert named parameters to PostgreSQL style
                pg_params = list(params.values())
                rows = await conn.fetch(optimized_sql, *pg_params)
            else:
                rows = await conn.fetch(optimized_sql)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to execute PostgreSQL query: {e}")
            logger.error(f"SQL: {sql}")
            logger.error(f"Params: {params}")
            raise
    
    async def execute_many(self, conn: asyncpg.Connection, sql: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute multiple queries with different parameters."""
        try:
            # Optimize query for PostgreSQL
            optimized_sql = self.optimize_query(sql)
            
            # Convert to PostgreSQL parameter style
            pg_params_list = [list(params.values()) for params in params_list]
            
            # Execute all queries
            await conn.executemany(optimized_sql, pg_params_list)
            return len(params_list)
            
        except Exception as e:
            logger.error(f"Failed to execute many PostgreSQL queries: {e}")
            logger.error(f"SQL: {sql}")
            raise
    
    async def begin_transaction(self, conn: asyncpg.Connection):
        """Begin a transaction."""
        await conn.execute("BEGIN")
    
    async def commit_transaction(self, conn: asyncpg.Connection):
        """Commit a transaction."""
        await conn.execute("COMMIT")
    
    async def rollback_transaction(self, conn: asyncpg.Connection):
        """Rollback a transaction."""
        await conn.execute("ROLLBACK")
    
    def get_connection_string(self) -> str:
        """Get the PostgreSQL connection string."""
        return f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
    
    def get_dialect(self) -> str:
        """Get the SQL dialect for PostgreSQL."""
        return "postgresql"
    
    def get_supported_features(self) -> List[str]:
        """Get list of supported features for PostgreSQL."""
        return [
            "transactions",
            "foreign_keys",
            "indexes",
            "views",
            "triggers",
            "stored_procedures",
            "full_text_search",
            "json_functions",
            "jsonb_functions",
            "window_functions",
            "common_table_expressions",
            "recursive_queries",
            "partitioning",
            "replication",
            "clustering",
            "materialized_views",
            "partial_indexes",
            "expression_indexes",
            "gin_indexes",
            "gist_indexes",
            "brin_indexes",
            "array_types",
            "range_types",
            "geometric_types",
            "network_types",
            "uuid_types",
            "xml_types",
            "full_text_search",
            "regular_expressions",
            "aggregate_functions",
            "window_functions"
        ]
    
    def optimize_query(self, sql: str) -> str:
        """Optimize a query for PostgreSQL."""
        # PostgreSQL-specific optimizations
        optimized = sql
        
        # Add EXPLAIN ANALYZE for debugging
        if self.config.echo:
            optimized = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {optimized}"
        
        # Optimize LIMIT clauses
        if "LIMIT" in optimized.upper():
            # PostgreSQL can optimize LIMIT with proper indexes
            pass
        
        # Optimize ORDER BY with LIMIT
        if "ORDER BY" in optimized.upper() and "LIMIT" in optimized.upper():
            # PostgreSQL can optimize ORDER BY + LIMIT
            pass
        
        # Optimize JOIN operations
        if "JOIN" in optimized.upper():
            # PostgreSQL can optimize JOINs with proper statistics
            pass
        
        # Optimize GROUP BY
        if "GROUP BY" in optimized.upper():
            # PostgreSQL can optimize GROUP BY with proper indexes
            pass
        
        return optimized
    
    def get_parameter_style(self) -> str:
        """Get the parameter style for PostgreSQL."""
        return "positional"  # PostgreSQL uses $1, $2, etc.
    
    def escape_identifier(self, identifier: str) -> str:
        """Escape an identifier for PostgreSQL."""
        return f'"{identifier}"'
    
    def get_auto_increment_sql(self) -> str:
        """Get the auto-increment SQL for PostgreSQL."""
        return "SERIAL"
    
    async def create_table(self, table_name: str, columns: List[Dict[str, Any]]):
        """Create a table with PostgreSQL-specific optimizations."""
        column_defs = []
        for column in columns:
            name = column['name']
            type_name = column['type']
            nullable = column.get('nullable', True)
            primary_key = column.get('primary_key', False)
            auto_increment = column.get('auto_increment', False)
            default = column.get('default')
            
            # Build column definition
            col_def = f'"{name}" {type_name}'
            
            if not nullable:
                col_def += " NOT NULL"
            
            if default is not None:
                if isinstance(default, str):
                    col_def += f" DEFAULT '{default}'"
                else:
                    col_def += f" DEFAULT {default}"
            
            if primary_key:
                col_def += " PRIMARY KEY"
                if auto_increment:
                    col_def += " SERIAL"
            
            column_defs.append(col_def)
        
        # Create table with PostgreSQL optimizations
        sql = f"""
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {', '.join(column_defs)}
        )
        """
        
        async with self.get_connection() as conn:
            await self.execute_query(conn, sql)
            
            # Create indexes for better performance
            await self._create_default_indexes(conn, table_name, columns)
    
    async def _create_default_indexes(self, conn: asyncpg.Connection, table_name: str, columns: List[Dict[str, Any]]):
        """Create default indexes for better performance."""
        for column in columns:
            if column.get('index', False):
                index_name = f"idx_{table_name}_{column['name']}"
                sql = f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table_name}" ("{column["name"]}")'
                await self.execute_query(conn, sql)
    
    async def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table information."""
        sql = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = $1
        ORDER BY ordinal_position
        """
        return await self.execute(sql, {"table_name": table_name})
    
    async def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a table."""
        sql = """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = $1
        """
        return await self.execute(sql, {"table_name": table_name})
    
    async def analyze_table(self, table_name: str):
        """Analyze a table for better query planning."""
        sql = f'ANALYZE "{table_name}"'
        await self.execute(sql)
    
    async def vacuum_table(self, table_name: str):
        """Vacuum a table."""
        sql = f'VACUUM "{table_name}"'
        await self.execute(sql)
    
    async def reindex_table(self, table_name: str):
        """Reindex a table."""
        sql = f'REINDEX TABLE "{table_name}"'
        await self.execute(sql)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get PostgreSQL statistics."""
        sql = "SELECT * FROM pg_stat_database WHERE datname = current_database()"
        return await self.execute(sql)
    
    async def get_query_statistics(self) -> List[Dict[str, Any]]:
        """Get query statistics if pg_stat_statements is available."""
        try:
            sql = """
            SELECT query, calls, total_time, mean_time, rows
            FROM pg_stat_statements
            WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
            ORDER BY total_time DESC
            LIMIT 10
            """
            return await self.execute(sql)
        except:
            return []
    
    async def get_locks(self) -> List[Dict[str, Any]]:
        """Get current locks."""
        sql = """
        SELECT locktype, database, relation, page, tuple, virtualxid, transactionid, classid, objid, objsubid, virtualtransaction, pid, mode, granted
        FROM pg_locks
        """
        return await self.execute(sql)
    
    async def kill_backend(self, pid: int):
        """Kill a PostgreSQL backend."""
        sql = f"SELECT pg_terminate_backend({pid})"
        await self.execute(sql)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get PostgreSQL performance statistics."""
        stats = self.get_pool_stats()
        
        # Add PostgreSQL-specific stats
        stats.update({
            'host': self.config.host,
            'port': self.config.port,
            'database': self.config.database,
            'dialect': 'postgresql',
            'features': self.get_supported_features()
        })
        
        return stats 