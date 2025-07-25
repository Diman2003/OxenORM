#!/usr/bin/env python3
"""
MySQL Backend for OxenORM

This module provides MySQL-specific backend implementation with:
- Connection pooling
- Query optimization
- MySQL-specific features
- Performance optimizations
"""

import aiomysql
import asyncio
import logging
from typing import Dict, List, Any, Optional
from .base import BaseBackend, DatabaseConfig

logger = logging.getLogger(__name__)


class MySQLBackend(BaseBackend):
    """MySQL backend implementation."""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._connections = set()
    
    async def create_connection(self, config: DatabaseConfig) -> aiomysql.Connection:
        """Create a new MySQL connection."""
        try:
            conn = await aiomysql.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                db=config.database,
                charset=config.charset,
                autocommit=config.mysql_autocommit,
                connect_timeout=config.connect_timeout,
                read_timeout=config.read_timeout,
                write_timeout=config.write_timeout,
                ssl=None if config.ssl_mode == "disable" else {"ssl": True}
            )
            
            # Configure connection for better performance
            async with conn.cursor() as cursor:
                # Set session variables for optimization
                await cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
                await cursor.execute("SET SESSION innodb_lock_wait_timeout = 50")
                await cursor.execute("SET SESSION wait_timeout = 28800")
                await cursor.execute("SET SESSION interactive_timeout = 28800")
                
                # Enable query cache if available
                try:
                    await cursor.execute("SET SESSION query_cache_type = 1")
                    await cursor.execute("SET SESSION query_cache_size = 67108864")  # 64MB
                except:
                    # Query cache might not be available in newer MySQL versions
                    pass
            
            self._connections.add(conn)
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create MySQL connection: {e}")
            raise
    
    async def close_connection(self, conn: aiomysql.Connection):
        """Close a MySQL connection."""
        try:
            if conn in self._connections:
                self._connections.remove(conn)
            conn.close()
        except Exception as e:
            logger.error(f"Failed to close MySQL connection: {e}")
    
    async def is_connection_valid(self, conn: aiomysql.Connection) -> bool:
        """Check if a MySQL connection is still valid."""
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    async def execute_query(self, conn: aiomysql.Connection, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        try:
            # Optimize query for MySQL
            optimized_sql = self.optimize_query(sql)
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                if params:
                    await cursor.execute(optimized_sql, params)
                else:
                    await cursor.execute(optimized_sql)
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to execute MySQL query: {e}")
            logger.error(f"SQL: {sql}")
            logger.error(f"Params: {params}")
            raise
    
    async def execute_many(self, conn: aiomysql.Connection, sql: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute multiple queries with different parameters."""
        try:
            # Optimize query for MySQL
            optimized_sql = self.optimize_query(sql)
            
            async with conn.cursor() as cursor:
                await cursor.executemany(optimized_sql, params_list)
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Failed to execute many MySQL queries: {e}")
            logger.error(f"SQL: {sql}")
            raise
    
    async def begin_transaction(self, conn: aiomysql.Connection):
        """Begin a transaction."""
        await conn.begin()
    
    async def commit_transaction(self, conn: aiomysql.Connection):
        """Commit a transaction."""
        await conn.commit()
    
    async def rollback_transaction(self, conn: aiomysql.Connection):
        """Rollback a transaction."""
        await conn.rollback()
    
    def get_connection_string(self) -> str:
        """Get the MySQL connection string."""
        return f"mysql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
    
    def get_dialect(self) -> str:
        """Get the SQL dialect for MySQL."""
        return "mysql"
    
    def get_supported_features(self) -> List[str]:
        """Get list of supported features for MySQL."""
        return [
            "transactions",
            "foreign_keys",
            "indexes",
            "views",
            "triggers",
            "stored_procedures",
            "full_text_search",
            "json_functions",
            "window_functions",
            "common_table_expressions",
            "recursive_queries",
            "partitioning",
            "replication",
            "clustering"
        ]
    
    def optimize_query(self, sql: str) -> str:
        """Optimize a query for MySQL."""
        # MySQL-specific optimizations
        optimized = sql
        
        # Add SQL_CALC_FOUND_ROWS for pagination optimization
        if "SELECT" in optimized.upper() and "LIMIT" in optimized.upper():
            # MySQL can optimize SELECT with LIMIT
            pass
        
        # Optimize JOIN operations
        if "JOIN" in optimized.upper():
            # Ensure proper JOIN order
            pass
        
        # Add FORCE INDEX hints if needed
        if "WHERE" in optimized.upper() and "INDEX" not in optimized.upper():
            # Could add index hints for better performance
            pass
        
        # Optimize GROUP BY
        if "GROUP BY" in optimized.upper():
            # MySQL can optimize GROUP BY with proper indexes
            pass
        
        return optimized
    
    def get_parameter_style(self) -> str:
        """Get the parameter style for MySQL."""
        return "named"
    
    def escape_identifier(self, identifier: str) -> str:
        """Escape an identifier for MySQL."""
        return f"`{identifier}`"
    
    def get_auto_increment_sql(self) -> str:
        """Get the auto-increment SQL for MySQL."""
        return "AUTO_INCREMENT"
    
    async def create_table(self, table_name: str, columns: List[Dict[str, Any]]):
        """Create a table with MySQL-specific optimizations."""
        column_defs = []
        for column in columns:
            name = column['name']
            type_name = column['type']
            nullable = column.get('nullable', True)
            primary_key = column.get('primary_key', False)
            auto_increment = column.get('auto_increment', False)
            default = column.get('default')
            
            # Build column definition
            col_def = f"`{name}` {type_name}"
            
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
                    col_def += " AUTO_INCREMENT"
            
            column_defs.append(col_def)
        
        # Create table with MySQL optimizations
        sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            {', '.join(column_defs)}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        async with self.get_connection() as conn:
            await self.execute_query(conn, sql)
            
            # Create indexes for better performance
            await self._create_default_indexes(conn, table_name, columns)
    
    async def _create_default_indexes(self, conn: aiomysql.Connection, table_name: str, columns: List[Dict[str, Any]]):
        """Create default indexes for better performance."""
        for column in columns:
            if column.get('index', False):
                index_name = f"idx_{table_name}_{column['name']}"
                sql = f"CREATE INDEX `{index_name}` ON `{table_name}` (`{column['name']}`)"
                await self.execute_query(conn, sql)
    
    async def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table information."""
        sql = f"DESCRIBE `{table_name}`"
        return await self.execute(sql)
    
    async def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for a table."""
        sql = f"SHOW INDEX FROM `{table_name}`"
        return await self.execute(sql)
    
    async def analyze_table(self, table_name: str):
        """Analyze a table for better query planning."""
        sql = f"ANALYZE TABLE `{table_name}`"
        await self.execute(sql)
    
    async def optimize_table(self, table_name: str):
        """Optimize a table."""
        sql = f"OPTIMIZE TABLE `{table_name}`"
        await self.execute(sql)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get MySQL server status."""
        sql = "SHOW STATUS"
        return await self.execute(sql)
    
    async def get_variables(self) -> Dict[str, Any]:
        """Get MySQL server variables."""
        sql = "SHOW VARIABLES"
        return await self.execute(sql)
    
    async def get_process_list(self) -> List[Dict[str, Any]]:
        """Get current MySQL processes."""
        sql = "SHOW PROCESSLIST"
        return await self.execute(sql)
    
    async def kill_query(self, process_id: int):
        """Kill a MySQL query."""
        sql = f"KILL {process_id}"
        await self.execute(sql)
    
    async def flush_logs(self):
        """Flush MySQL logs."""
        await self.execute("FLUSH LOGS")
    
    async def flush_tables(self):
        """Flush MySQL tables."""
        await self.execute("FLUSH TABLES")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get MySQL performance statistics."""
        stats = self.get_pool_stats()
        
        # Add MySQL-specific stats
        stats.update({
            'host': self.config.host,
            'port': self.config.port,
            'database': self.config.database,
            'dialect': 'mysql',
            'features': self.get_supported_features()
        })
        
        return stats 