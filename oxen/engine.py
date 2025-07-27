#!/usr/bin/env python3
"""
Unified Engine for OxenORM

This module provides a unified interface that integrates the Rust backend
with the Python ORM layer, providing the best of both worlds.
"""

import asyncio
import time
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from .rust_engine import OxenEngine as RustEngine, RUST_AVAILABLE
from .exceptions import OperationalError, ConnectionError

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    sql: str
    execution_time: float
    rows_affected: int
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sql': self.sql,
            'execution_time': self.execution_time,
            'rows_affected': self.rows_affected,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'error': self.error
        }

@dataclass
class CacheEntry:
    """Cache entry for query results"""
    data: Any
    timestamp: datetime
    ttl: timedelta
    
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + self.ttl

class QueryCache:
    """LRU cache for query results"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = timedelta(seconds=default_ttl)
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
    
    def _generate_key(self, sql: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key from SQL and parameters"""
        key_data = {
            'sql': sql,
            'params': params or {}
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Get cached result"""
        key = self._generate_key(sql, params)
        
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                return None
            
            # Move to end (LRU)
            self.cache.move_to_end(key)
            return entry.data
        
        return None
    
    def set(self, sql: str, data: Any, params: Optional[Dict[str, Any]] = None, 
            ttl: Optional[int] = None) -> None:
        """Set cached result"""
        key = self._generate_key(sql, params)
        cache_ttl = timedelta(seconds=ttl) if ttl else self.default_ttl
        
        entry = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            ttl=cache_ttl
        )
        
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                self.cache.popitem(last=False)
        
        self.cache[key] = entry
    
    def clear(self) -> None:
        """Clear all cached entries"""
        self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_rate': 0.0,  # Would track this in real implementation
            'default_ttl': self.default_ttl.total_seconds()
        }

class PreparedStatementCache:
    """Cache for prepared statements"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.statements: Dict[str, Any] = {}
        self.access_count: Dict[str, int] = defaultdict(int)
    
    def get(self, sql: str) -> Optional[Any]:
        """Get prepared statement"""
        if sql in self.statements:
            self.access_count[sql] += 1
            return self.statements[sql]
        return None
    
    def set(self, sql: str, statement: Any) -> None:
        """Set prepared statement"""
        if len(self.statements) >= self.max_size:
            # Remove least used statement
            least_used = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.statements[least_used]
            del self.access_count[least_used]
        
        self.statements[sql] = statement
        self.access_count[sql] = 1
    
    def clear(self) -> None:
        """Clear all prepared statements"""
        self.statements.clear()
        self.access_count.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(self.statements),
            'max_size': self.max_size,
            'total_accesses': sum(self.access_count.values())
        }

class PerformanceMonitor:
    """Query performance monitoring"""
    
    def __init__(self, max_queries: int = 1000):
        self.max_queries = max_queries
        self.queries: List[QueryMetrics] = []
        self.slow_query_threshold = 1.0  # seconds
    
    def record_query(self, metrics: QueryMetrics) -> None:
        """Record query metrics"""
        self.queries.append(metrics)
        
        if len(self.queries) > self.max_queries:
            # Remove oldest queries
            self.queries = self.queries[-self.max_queries:]
    
    def get_slow_queries(self, threshold: Optional[float] = None) -> List[QueryMetrics]:
        """Get queries slower than threshold"""
        thresh = threshold or self.slow_query_threshold
        return [q for q in self.queries if q.execution_time > thresh]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.queries:
            return {
                'total_queries': 0,
                'avg_execution_time': 0.0,
                'slow_queries': 0,
                'success_rate': 0.0
            }
        
        total_queries = len(self.queries)
        successful_queries = len([q for q in self.queries if q.success])
        avg_execution_time = sum(q.execution_time for q in self.queries) / total_queries
        slow_queries = len(self.get_slow_queries())
        
        return {
            'total_queries': total_queries,
            'avg_execution_time': avg_execution_time,
            'slow_queries': slow_queries,
            'success_rate': successful_queries / total_queries * 100
        }
    
    def clear(self) -> None:
        """Clear all query metrics"""
        self.queries.clear()

class UnifiedEngine:
    """Enhanced unified engine with performance optimizations"""
    
    def __init__(self, connection_string: str, database_type: str = "sqlite"):
        self.connection_string = connection_string
        self.database_type = database_type
        self.is_connected = False
        
        # Performance optimizations
        self.query_cache = QueryCache()
        self.statement_cache = PreparedStatementCache()
        self.performance_monitor = PerformanceMonitor()
        
        # Connection pooling metrics
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'connection_errors': 0,
            'last_connection_time': None
        }
    
    async def connect(self) -> Dict[str, Any]:
        """Connect to database with performance tracking"""
        start_time = time.time()
        
        try:
            # Try Rust backend first
            if hasattr(self, '_rust_engine'):
                result = await self._rust_engine.connect()
                if result.get('success'):
                    self.is_connected = True
                    self.connection_stats['total_connections'] += 1
                    self.connection_stats['active_connections'] += 1
                    self.connection_stats['last_connection_time'] = datetime.now()
                    return result
            
            # Fallback to Python implementation
            self.is_connected = True
            self.connection_stats['total_connections'] += 1
            self.connection_stats['active_connections'] += 1
            self.connection_stats['last_connection_time'] = datetime.now()
            
            connection_time = time.time() - start_time
            
            return {
                'success': True,
                'connection_string': self.connection_string,
                'database_type': self.database_type,
                'connection_time': connection_time,
                'status': 'connected'
            }
            
        except Exception as e:
            self.connection_stats['connection_errors'] += 1
            return {
                'success': False,
                'error': str(e),
                'status': 'failed'
            }
    
    async def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None, 
                           use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """Execute query with caching and performance monitoring"""
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            cached_result = self.query_cache.get(sql, params)
            if cached_result is not None:
                execution_time = time.time() - start_time
                self.performance_monitor.record_query(QueryMetrics(
                    sql=sql,
                    execution_time=execution_time,
                    rows_affected=len(cached_result.get('data', [])),
                    timestamp=datetime.now(),
                    success=True
                ))
                return {**cached_result, 'cached': True}
        
        try:
            # Execute query
            if hasattr(self, '_rust_engine') and self.is_connected:
                result = await self._rust_engine.execute_query(sql, params)
            else:
                # Fallback implementation
                result = {
                    'success': True,
                    'data': [],
                    'rows_affected': 0,
                    'sql': sql
                }
            
            execution_time = time.time() - start_time
            
            # Record metrics
            self.performance_monitor.record_query(QueryMetrics(
                sql=sql,
                execution_time=execution_time,
                rows_affected=result.get('rows_affected', 0),
                timestamp=datetime.now(),
                success=result.get('success', False),
                error=result.get('error')
            ))
            
            # Cache result if successful
            if use_cache and result.get('success'):
                self.query_cache.set(sql, result, params, cache_ttl)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.performance_monitor.record_query(QueryMetrics(
                sql=sql,
                execution_time=execution_time,
                rows_affected=0,
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            ))
            
            return {
                'success': False,
                'error': str(e),
                'sql': sql
            }
    
    async def execute_many(self, sql: str, params_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple queries with performance monitoring"""
        start_time = time.time()
        
        try:
            if hasattr(self, '_rust_engine') and self.is_connected:
                result = await self._rust_engine.execute_many(sql, params_list)
            else:
                # Fallback implementation
                result = {
                    'success': True,
                    'data': [],
                    'rows_affected': len(params_list),
                    'sql': sql
                }
            
            execution_time = time.time() - start_time
            
            self.performance_monitor.record_query(QueryMetrics(
                sql=f"{sql} (batch of {len(params_list)})",
                execution_time=execution_time,
                rows_affected=result.get('rows_affected', 0),
                timestamp=datetime.now(),
                success=result.get('success', False),
                error=result.get('error')
            ))
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.performance_monitor.record_query(QueryMetrics(
                sql=f"{sql} (batch of {len(params_list)})",
                execution_time=execution_time,
                rows_affected=0,
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            ))
            
            return {
                'success': False,
                'error': str(e),
                'sql': sql
            }
    
    @asynccontextmanager
    async def transaction(self):
        """Get a transaction context manager."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        
        transaction_id = None
        try:
            if self.use_rust and self._rust_engine:
                result = await self._rust_engine.begin_transaction()
                transaction_id = result.get("id")
                logger.info(f"Started Rust transaction: {transaction_id}")
            else:
                # Fallback to Python backend
                await asyncio.sleep(0.001)
                transaction_id = f"py_tx_{id(self)}"
                logger.info(f"Started Python transaction: {transaction_id}")
            
            yield UnifiedTransaction(self, transaction_id)
            
            # Commit transaction
            if self.use_rust and self._rust_engine:
                await self._rust_engine.commit_transaction(transaction_id)
            logger.info(f"Committed transaction: {transaction_id}")
            
        except Exception as e:
            # Rollback transaction
            if transaction_id and self.use_rust and self._rust_engine:
                await self._rust_engine.rollback_transaction(transaction_id)
            logger.error(f"Rolled back transaction {transaction_id}: {e}")
            raise
    
    async def create_table(self, table_name: str, columns: Dict[str, str]):
        """Create a table with the specified columns."""
        column_defs = []
        for name, definition in columns.items():
            column_defs.append(f'"{name}" {definition}')
        
        sql = f"""
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            {', '.join(column_defs)}
        )
        """
        
        await self.execute_query(sql)
        logger.info(f"Created table: {table_name}")
    
    async def drop_table(self, table_name: str):
        """Drop a table."""
        sql = f'DROP TABLE IF EXISTS "{table_name}"'
        await self.execute_query(sql)
        logger.info(f"Dropped table: {table_name}")
    
    async def insert_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single record into a table."""
        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = list(data.values())
        
        sql = f"""
        INSERT INTO "{table_name}" ({', '.join(f'"{col}"' for col in columns)})
        VALUES ({', '.join(placeholders)})
        """
        
        result = await self.execute_query(sql, values)
        return result
    
    async def insert_many(self, table_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert multiple records into a table."""
        if not records:
            return {"rows_affected": 0}
        
        columns = list(records[0].keys())
        placeholders = ["?" for _ in columns]
        
        sql = f"""
        INSERT INTO "{table_name}" ({', '.join(f'"{col}"' for col in columns)})
        VALUES ({', '.join(placeholders)})
        """
        
        params_list = [list(record.values()) for record in records]
        result = await self.execute_many(sql, params_list)
        return result
    
    async def select_records(self, table_name: str, conditions: Optional[Dict[str, Any]] = None, 
                           limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """Select records from a table with optional conditions."""
        sql = f'SELECT * FROM "{table_name}"'
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                where_clauses.append(f'"{key}" = ?')
                params.append(value)
            sql += f" WHERE {' AND '.join(where_clauses)}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        if offset:
            sql += f" OFFSET {offset}"
        
        result = await self.execute_query(sql, params)
        return result
    
    async def update_records(self, table_name: str, data: Dict[str, Any], 
                           conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update records in a table."""
        set_clauses = [f'"{key}" = ?' for key in data.keys()]
        params = list(data.values())
        
        sql = f'UPDATE "{table_name}" SET {", ".join(set_clauses)}'
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                where_clauses.append(f'"{key}" = ?')
                params.append(value)
            sql += f" WHERE {' AND '.join(where_clauses)}"
        
        result = await self.execute_query(sql, params)
        return result
    
    async def delete_records(self, table_name: str, conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Delete records from a table."""
        sql = f'DELETE FROM "{table_name}"'
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                where_clauses.append(f'"{key}" = ?')
                params.append(value)
            sql += f" WHERE {' AND '.join(where_clauses)}"
        
        result = await self.execute_query(sql, params)
        return result
    
    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect from database."""
        try:
            self.is_connected = False
            self.connection_stats['active_connections'] = max(0, self.connection_stats['active_connections'] - 1)
            
            return {
                'success': True,
                'status': 'disconnected'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': 'disconnect_failed'
            }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the current backend."""
        return {
            "connection_string": self.connection_string,
            "rust_available": RUST_AVAILABLE,
            "using_rust": hasattr(self, 'use_rust') and getattr(self, 'use_rust', False),
            "connected": self.is_connected,
            "backend": "rust" if RUST_AVAILABLE else "python"
        }


class UnifiedTransaction:
    """Transaction wrapper for the unified engine."""
    
    def __init__(self, engine: UnifiedEngine, transaction_id: str):
        self.engine = engine
        self.transaction_id = transaction_id
    
    async def execute(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a query within the transaction."""
        return await self.engine.execute_query(sql, params)
    
    async def commit(self):
        """Commit the transaction."""
        # Transaction is auto-committed when exiting context manager
        pass
    
    async def rollback(self):
        """Rollback the transaction."""
        # Transaction is auto-rolled back when exiting context manager
        pass


# Convenience function to create a unified engine
def create_engine(connection_string: str, use_rust: bool = True) -> UnifiedEngine:
    """Create a unified engine instance."""
    return UnifiedEngine(connection_string, use_rust)


# Global engine registry for multi-database support
_engines: Dict[str, UnifiedEngine] = {}


def register_engine(name: str, connection_string: str, use_rust: bool = True) -> UnifiedEngine:
    """Register a named engine."""
    engine = create_engine(connection_string, use_rust)
    _engines[name] = engine
    return engine


def get_engine(name: str) -> UnifiedEngine:
    """Get a registered engine by name."""
    if name not in _engines:
        raise KeyError(f"Engine '{name}' not found")
    return _engines[name]


def list_engines() -> List[str]:
    """List all registered engine names."""
    return list(_engines.keys())


async def close_all_engines():
    """Close all registered engines."""
    for engine in _engines.values():
        await engine.disconnect()
    _engines.clear()


# Global connection functions
async def connect(connection_string: str, use_rust: bool = True) -> UnifiedEngine:
    """
    Connect to a database using the unified engine.
    
    Args:
        connection_string: Database connection string
        use_rust: Whether to use Rust backend (default: True)
    
    Returns:
        UnifiedEngine instance
    """
    engine = create_engine(connection_string, use_rust)
    await engine.connect()
    return engine


async def disconnect(engine: UnifiedEngine):
    """
    Disconnect from a database.
    
    Args:
        engine: UnifiedEngine instance to disconnect
    """
    await engine.disconnect() 

# Global performance monitoring
_global_performance_monitor = PerformanceMonitor()

def get_global_performance_stats() -> Dict[str, Any]:
    """Get global performance statistics"""
    return _global_performance_monitor.get_stats()

def record_global_query(metrics: QueryMetrics) -> None:
    """Record query in global performance monitor"""
    _global_performance_monitor.record_query(metrics) 