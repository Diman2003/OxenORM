#!/usr/bin/env python3
"""
Unified Engine for OxenORM

This module provides a unified interface that integrates the Rust backend
with the Python ORM layer, providing the best of both worlds.
"""

import asyncio
import time as time_module
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date, time
from contextlib import asynccontextmanager
from decimal import Decimal

from .rust_engine import OxenEngine as RustEngine, RUST_AVAILABLE
from .exceptions import OperationalError, ConnectionError
from oxen.query_optimizer import optimize_query, get_performance_stats
from oxen.monitoring import record_query_metric, record_cache_metric, record_connection_metric

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
        # Convert non-JSON-serializable objects to strings
        def convert_for_json(obj):
            if isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(v) for v in obj]
            elif hasattr(obj, 'as_tuple'):  # Decimal objects
                return str(obj)
            elif isinstance(obj, (datetime, date, time)):
                return str(obj)
            elif hasattr(obj, 'pk'):  # Model instances
                return obj.pk
            elif hasattr(obj, 'pk_value'):  # Lazy objects
                return obj.pk_value
            else:
                return obj
        
        key_data = {
            'sql': sql,
            'params': convert_for_json(params or {})
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
            'hits': 0,  # Would track this in real implementation
            'misses': 0,  # Would track this in real implementation
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
                'average_time': 0.0,
                'min_time': 0.0,
                'max_time': 0.0,
                'slow_queries': 0,
                'success_rate': 0.0,
                'cache_hit_rate': 0.0
            }
        
        total_queries = len(self.queries)
        successful_queries = len([q for q in self.queries if q.success])
        execution_times = [q.execution_time for q in self.queries]
        avg_execution_time = sum(execution_times) / total_queries
        slow_queries = len(self.get_slow_queries())
        
        return {
            'total_queries': total_queries,
            'average_time': avg_execution_time,
            'min_time': min(execution_times) if execution_times else 0.0,
            'max_time': max(execution_times) if execution_times else 0.0,
            'slow_queries': slow_queries,
            'success_rate': successful_queries / total_queries * 100,
            'cache_hit_rate': 0.0  # Placeholder for cache hit rate
        }
    
    def clear(self) -> None:
        """Clear all query metrics"""
        self.queries.clear()

class UnifiedEngine:
    """Unified database engine with Rust backend integration."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.rust_engine = None
        self.query_cache = QueryCache()
        self.prepared_statements = PreparedStatementCache()
        self.performance_monitor = PerformanceMonitor()
        self.query_optimizer = None  # Will be initialized when needed
        
        # Parse connection string
        if connection_string.startswith('sqlite://'):
            self.db_type = 'sqlite'
            self.db_path = connection_string.replace('sqlite://', '')
        elif connection_string.startswith('postgresql://'):
            self.db_type = 'postgresql'
            self.db_url = connection_string
        elif connection_string.startswith('mysql://'):
            self.db_type = 'mysql'
            self.db_url = connection_string
        else:
            raise ValueError(f"Unsupported database type: {connection_string}")
    
    async def connect(self) -> Dict[str, Any]:
        """Connect to the database."""
        try:
            if self.db_type == 'sqlite':
                # Initialize Rust backend for SQLite
                from oxen.rust_engine import init_rust_engine
                self.rust_engine = await init_rust_engine(self.connection_string)
                
                # Test connection with direct SQLite query
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
                
                # Record connection metric
                record_connection_metric(1, 1)  # Pool size 1, 1 active connection
                
                return {
                    'success': True,
                    'message': f'Connected to SQLite database: {self.db_path}',
                    'backend': 'rust',
                    'database_type': self.db_type
                }
            else:
                # For other databases, use Python backend
                return {
                    'success': True,
                    'message': f'Connected to {self.db_type} database',
                    'backend': 'python',
                    'database_type': self.db_type
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'database_type': self.db_type
            }
    
    async def execute_query(self, sql: str, params: Optional[List[Any]] = None, 
                           use_cache: bool = True, cache_ttl: Optional[int] = None) -> Dict[str, Any]:
        """Execute a query with optimization and monitoring."""
        start_time = time_module.time()
        
        try:
            # Execute the query
            if self.db_type == 'sqlite' and self.rust_engine:
                result = await self._execute_sqlite_query(sql, params)
            else:
                result = await self._execute_python_query(sql, params)
            
            execution_time = time_module.time() - start_time
            rows_affected = result.get('rows_affected', 0)
            success = result.get('success', False)
            
            # Record monitoring metrics
            record_query_metric(execution_time, success, rows_affected)
            
            # Record cache metrics if using cache
            if use_cache:
                cache_hit = result.get('cached', False)
                record_cache_metric(cache_hit)
            
            # Optimize and analyze the query
            if self.query_optimizer is None:
                from oxen.query_optimizer import get_optimizer
                self.query_optimizer = get_optimizer()
            
            query_plan = self.query_optimizer.optimize_query(sql, execution_time, rows_affected)
            
            # Add optimization info to result
            result['optimization'] = {
                'performance_score': query_plan.performance_score,
                'suggestions': query_plan.optimization_suggestions,
                'execution_time': execution_time
            }
            
            # Record performance metrics
            self.performance_monitor.record_query(QueryMetrics(
                sql=sql,
                execution_time=execution_time,
                rows_affected=rows_affected,
                timestamp=datetime.now(),
                success=result.get('success', False),
                error=result.get('error')
            ))
            
            return result
            
        except Exception as e:
            execution_time = time_module.time() - start_time
            
            # Record failed query metrics
            record_query_metric(execution_time, False, 0)
            
            # Record failed query
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
                'execution_time': execution_time
            }
    
    async def _execute_sqlite_query(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a query using SQLite directly."""
        import sqlite3
        import asyncio
        
        def _execute_sync():
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                # Handle different query types
                if sql.strip().upper().startswith('SELECT'):
                    # SELECT query
                    rows = cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    data = [dict(zip(columns, row)) for row in rows]
                    
                    conn.commit()
                    conn.close()
                    
                    return {
                        'success': True,
                        'data': data,
                        'rows_affected': len(data),
                        'sql': sql
                    }
                else:
                    # INSERT, UPDATE, DELETE query
                    conn.commit()
                    last_id = cursor.lastrowid
                    rows_affected = cursor.rowcount
                    conn.close()
                    
                    return {
                        'success': True,
                        'rows_affected': rows_affected,
                        'last_id': last_id,
                        'sql': sql
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'sql': sql
                }
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute_sync)
    
    async def _execute_python_query(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute query using Python backend (fallback)."""
        # Simple fallback implementation for non-SQLite databases
        # In a real implementation, this would use appropriate database drivers
        return {
            'success': False,
            'error': 'Python backend not implemented for this database type',
            'data': [],
            'rows_affected': 0
        }
    
    async def execute_many(self, sql: str, params_list: List[List[Any]]) -> Dict[str, Any]:
        """Execute multiple queries with performance monitoring"""
        start_time = time_module.time()
        
        try:
            if hasattr(self, '_rust_engine') and self.is_connected:
                result = await self._rust_engine.execute_many(sql, params_list)
            else:
                # SQLite fallback implementation
                result = await self._execute_sqlite_many(sql, params_list)
            
            execution_time = time_module.time() - start_time
            
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
            execution_time = time_module.time() - start_time
            
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
    
    async def _execute_sqlite_many(self, sql: str, params_list: List[List[Any]]) -> Dict[str, Any]:
        """Execute multiple queries using SQLite directly."""
        import sqlite3
        import asyncio
        
        def _execute_sync():
            try:
                conn = sqlite3.connect(self.connection_string.replace('sqlite:///', ''))
                cursor = conn.cursor()
                
                # Execute all queries
                for params in params_list:
                    cursor.execute(sql, params)
                
                conn.commit()
                last_id = cursor.lastrowid
                rows_affected = cursor.rowcount
                conn.close()
                
                return {
                    'success': True,
                    'rows_affected': rows_affected,
                    'sql': sql,
                    'last_id': last_id
                }
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'sql': sql
                }
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute_sync)
    
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
        
        # Convert values to database-compatible format
        converted_values = []
        for value in data.values():
            if hasattr(value, 'as_tuple'):  # Decimal
                if 'postgresql' in self.connection_string.lower():
                    converted_values.append(float(value))  # PostgreSQL numeric
                else:
                    converted_values.append(str(value))  # SQLite text
            elif isinstance(value, (datetime, date, time)):
                if 'postgresql' in self.connection_string.lower():
                    # PostgreSQL expects proper date/time types
                    if isinstance(value, date):
                        converted_values.append(value)  # Keep as date object
                    elif isinstance(value, time):
                        converted_values.append(value)  # Keep as time object
                    elif isinstance(value, datetime):
                        converted_values.append(value)  # Keep as datetime object
                else:
                    converted_values.append(str(value))  # SQLite as string
            elif isinstance(value, dict):  # JSON field
                import json
                converted_values.append(json.dumps(value))
            elif isinstance(value, list):  # Array field
                import json
                converted_values.append(json.dumps(value))
            else:
                converted_values.append(value)
        
        # Use appropriate placeholders based on database type
        if 'postgresql' in self.connection_string.lower():
            placeholders = [f"${i+1}" for i in range(len(columns))]
        else:
            placeholders = ["?" for _ in columns]
        
        sql = self._generate_insert_sql(table_name, columns, placeholders)
        
        result = await self.execute_query(sql, converted_values)
        return result
    
    async def insert_many(self, table_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert multiple records into a table."""
        if not records:
            return {"success": True, "rows_affected": 0, "data": {"ids": []}}
        
        columns = list(records[0].keys())
        
        # Convert all records to database-compatible format
        converted_records = []
        for record in records:
            converted_record = {}
            for key, value in record.items():
                if hasattr(value, 'as_tuple'):  # Decimal
                    if 'postgresql' in self.connection_string.lower():
                        converted_record[key] = float(value)  # PostgreSQL numeric
                    else:
                        converted_record[key] = str(value)  # SQLite text
                elif isinstance(value, (datetime, date, time)):
                    if 'postgresql' in self.connection_string.lower():
                        # PostgreSQL expects proper date/time types
                        if isinstance(value, date):
                            converted_record[key] = value  # Keep as date object
                        elif isinstance(value, time):
                            converted_record[key] = value  # Keep as time object
                        elif isinstance(value, datetime):
                            converted_record[key] = value  # Keep as datetime object
                    else:
                        converted_record[key] = str(value)  # SQLite as string
                elif isinstance(value, dict):  # JSON field
                    import json
                    converted_record[key] = json.dumps(value)
                elif isinstance(value, list):  # Array field
                    import json
                    converted_record[key] = json.dumps(value)
                else:
                    converted_record[key] = value
            converted_records.append(converted_record)
        
        # Use appropriate placeholders based on database type
        if 'postgresql' in self.connection_string.lower():
            placeholders = [f"${i+1}" for i in range(len(columns))]
        else:
            placeholders = ["?" for _ in columns]
        
        sql = self._generate_insert_sql(table_name, columns, placeholders)
        
        params_list = [list(record.values()) for record in converted_records]
        result = await self.execute_many(sql, params_list)
        
        # Add generated IDs to result
        if result.get('success'):
            # For SQLite, we need to get the IDs by querying the last inserted rows
            # This is a simplified approach - in production, you might want to use a more robust method
            ids = []
            if len(records) > 0:
                # Get the last inserted ID and work backwards
                last_id = result.get('last_id', 0)
                for i in range(len(records)):
                    ids.append(last_id - len(records) + 1 + i)
            
            result['data'] = {'ids': ids}
        
        return result
    
    async def select_records(self, table_name: str, conditions: Optional[Dict[str, Any]] = None, 
                           limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """Select records from a table with optional conditions."""
        quoted_table = self._quote_identifier(table_name)
        sql = f'SELECT * FROM {quoted_table}'
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                quoted_key = self._quote_identifier(key)
                where_clauses.append(f'{quoted_key} = ?')
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
        # Convert values to database-compatible format
        converted_data = {}
        for key, value in data.items():
            if hasattr(value, 'as_tuple'):  # Decimal
                if 'postgresql' in self.connection_string.lower():
                    converted_data[key] = float(value)  # PostgreSQL numeric
                else:
                    converted_data[key] = str(value)  # SQLite text
            elif isinstance(value, (datetime, date, time)):
                if 'postgresql' in self.connection_string.lower():
                    # PostgreSQL expects proper date/time types
                    if isinstance(value, date):
                        converted_data[key] = value  # Keep as date object
                    elif isinstance(value, time):
                        converted_data[key] = value  # Keep as time object
                    elif isinstance(value, datetime):
                        converted_data[key] = value  # Keep as datetime object
                else:
                    converted_data[key] = str(value)  # SQLite as string
            elif isinstance(value, dict):  # JSON field
                import json
                converted_data[key] = json.dumps(value)
            elif isinstance(value, list):  # Array field
                import json
                converted_data[key] = json.dumps(value)
            else:
                converted_data[key] = value
        
        # Use appropriate placeholders based on database type
        if 'postgresql' in self.connection_string.lower():
            set_clauses = [f'"{key}" = ${i+1}' for i, key in enumerate(converted_data.keys())]
            params = list(converted_data.values())
            
            sql = f'UPDATE "{table_name}" SET {", ".join(set_clauses)}'
            
            if conditions:
                where_clauses = []
                for key, value in conditions.items():
                    param_index = len(params) + 1
                    where_clauses.append(f'"{key}" = ${param_index}')
                    params.append(value)
                sql += f" WHERE {' AND '.join(where_clauses)}"
        else:
            quoted_table = self._quote_identifier(table_name)
            set_clauses = [f'{self._quote_identifier(key)} = ?' for key in converted_data.keys()]
            params = list(converted_data.values())
            
            sql = f'UPDATE {quoted_table} SET {", ".join(set_clauses)}'
            
            if conditions:
                where_clauses = []
                for key, value in conditions.items():
                    quoted_key = self._quote_identifier(key)
                    where_clauses.append(f'{quoted_key} = ?')
                    params.append(value)
                sql += f" WHERE {' AND '.join(where_clauses)}"
        
        result = await self.execute_query(sql, params)
        return result
    
    async def delete_records(self, table_name: str, conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Delete records from a table."""
        quoted_table = self._quote_identifier(table_name)
        sql = f'DELETE FROM {quoted_table}'
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                quoted_key = self._quote_identifier(key)
                where_clauses.append(f'{quoted_key} = ?')
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

    def _quote_identifier(self, identifier: str) -> str:
        """Quote an identifier based on database type."""
        if 'mysql' in self.connection_string.lower():
            return f"`{identifier}`"
        else:
            return f'"{identifier}"'
    
    def _generate_insert_sql(self, table_name: str, columns: List[str], placeholders: List[str]) -> str:
        """Generate INSERT SQL with proper quoting."""
        quoted_table = self._quote_identifier(table_name)
        quoted_columns = [self._quote_identifier(col) for col in columns]
        
        return f"""
        INSERT INTO {quoted_table} ({', '.join(quoted_columns)})
        VALUES ({', '.join(placeholders)})
        """


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
    engine = UnifiedEngine(connection_string)
    
    # Initialize Rust backend if available and requested
    if use_rust and RUST_AVAILABLE:
        try:
            from .rust_bridge import OxenEngine
            engine._rust_engine = OxenEngine(connection_string)
            print(f"✅ Rust backend initialized for: {connection_string}")
        except Exception as e:
            print(f"⚠️  Failed to initialize Rust backend: {e}")
    
    return engine


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
    
    # Set the database connection for all models
    from oxen.models import set_database_for_models
    set_database_for_models(engine)
    
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