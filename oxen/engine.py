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
import os
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
        self.compiled_statement_cache = None
        self.performance_monitor = PerformanceMonitor()
        self.query_optimizer = None  # Will be initialized when needed
        self.is_connected = False
        self._connected = False
        self.connection_stats = {
            'pool_size': 0,
            'active_connections': 0,
        }
        # Table-epoch invalidation: increments on writes per table
        self._table_epochs: Dict[str, int] = {}
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
        self.use_rust = os.getenv('OXEN_RUST_BACKEND', '1') != '0'
        # Initialize compiled statement cache
        from oxen.compiled_statement_cache import CompiledStatementCache
        self.compiled_statement_cache = CompiledStatementCache(max_size=256)
    
    async def connect(self) -> Dict[str, Any]:
        """Connect to the database using the Rust backend for all dialects and prewarm compiled statement cache."""
        try:
            # Ensure SQLite file parent directory exists (avoids 'unable to open database file')
            if getattr(self, 'db_type', None) == 'sqlite':
                db_path = getattr(self, 'db_path', '')
                if db_path and ':memory:' not in db_path and not db_path.startswith('file::memory:'):
                    dirpath = os.path.dirname(db_path)
                    if dirpath:
                        try:
                            os.makedirs(dirpath, exist_ok=True)
                        except Exception:
                            pass

            if RUST_AVAILABLE and self.use_rust:
                if getattr(self, '_rust_engine', None) is None:
                    from .rust_bridge import OxenEngine as RustOxenEngine
                    self._rust_engine = RustOxenEngine(self.connection_string)
                result = await self._rust_engine.connect()
                self.is_connected = True
                self._connected = True
                self.rust_engine = self._rust_engine
                record_connection_metric(1, 1)
                try:
                    pool = await self._rust_engine.get_pool_status()
                    if isinstance(pool, dict):
                        self.connection_stats.update({
                            'pool_size': int(pool.get('pool_size', 1)),
                            'active_connections': int(pool.get('used_connections', 1)),
                        })
                except Exception:
                    self.connection_stats['active_connections'] = 1
                # Prewarm compiled statement cache with common queries
                from oxen.ir_sql_compiler import SQLCompiler, SelectIR
                common_irs = [
                    SelectIR(table='users', columns=['id', 'username'], limit=0),
                    SelectIR(table='posts', columns=['id', 'title'], limit=0),
                ]
                self.compiled_statement_cache.prewarm(SQLCompiler, common_irs)
                return {
                    'success': True,
                    'message': f'Connected to {self.db_type} database',
                    'backend': 'rust',
                    'database_type': self.db_type,
                    'details': result,
                }
            else:
                return {
                    'success': False,
                    'error': 'Rust backend not available or disabled (set OXEN_RUST_BACKEND=1 and build the Rust extension)',
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
        minimal_overhead = os.getenv('OXEN_MIN_OVERHEAD', '0') == '1'
        cache_enabled = os.getenv('OXEN_CACHE', '1') != '0'

        try:
            # Cache for read (SELECT) queries
            is_select = sql.lstrip().lower().startswith('select')
            tables_for_select = self._extract_tables(sql) if is_select else []
            cache_key_params = None
            if is_select and use_cache and cache_enabled:
                try:
                    epochs = {t: self._table_epochs.get(t, 0) for t in tables_for_select}
                    cache_key_params = {'params': params or [], '__epochs__': epochs}
                    cached = self.query_cache.get(sql, cache_key_params)
                    if cached is not None:
                        result = cached
                        result = dict(result) if isinstance(result, dict) else {'data': cached}
                        result['cached'] = True
                        result.setdefault('rows_affected', len(result.get('data') or []))
                        return result
                except Exception:
                    pass

            # Execute the query via Rust backend only
            if not getattr(self, '_rust_engine', None):
                # Try to initialize/connect Rust engine lazily
                await self.connect()
            result = await self._execute_rust_query(sql, params)
            
            # normalize success flag
            if 'success' not in result:
                result['success'] = result.get('error') is None

            execution_time = time_module.time() - start_time
            rows_affected = result.get('rows_affected', 0)
            success = result.get('success', False)
            
            # Write invalidation: bump table epoch
            if success and not is_select:
                try:
                    table = self._extract_write_table(sql)
                    if table:
                        self._table_epochs[table] = self._table_epochs.get(table, 0) + 1
                        # Optional: could purge cache entries here (not required since epochs gate keys)
                except Exception:
                    pass

            # Cache set for successful SELECT
            if success and is_select and use_cache and cache_enabled:
                try:
                    if cache_key_params is None:
                        epochs = {t: self._table_epochs.get(t, 0) for t in tables_for_select}
                        cache_key_params = {'params': params or [], '__epochs__': epochs}
                    self.query_cache.set(sql, result, cache_key_params, ttl=cache_ttl or int(os.getenv('OXEN_CACHE_TTL', '60')))
                except Exception:
                    pass

            if not minimal_overhead:
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
            
            if not minimal_overhead:
                # Record failed query metrics
                record_query_metric(execution_time, False, 0)
            
            if not minimal_overhead:
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
    
    def _extract_tables(self, sql: str) -> List[str]:
        """Very simple SQL scan to find table names after FROM and JOIN.
        Handles quoted identifiers with " and `.
        """
        s = sql.lower()
        tokens = s.replace('\n', ' ').replace('\t',' ').split()
        tables: List[str] = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok in ('from', 'join', 'update', 'into') and i + 1 < len(tokens):
                tbl = tokens[i+1]
                # strip quotes and aliases
                if tbl.startswith('"') and tbl.endswith('"') and len(tbl) > 1:
                    tbl = tbl.strip('"')
                if tbl.startswith('`') and tbl.endswith('`') and len(tbl) > 1:
                    tbl = tbl.strip('`')
                # drop schema prefix schema.table
                if '.' in tbl:
                    tbl = tbl.split('.')[-1]
                # remove trailing comma or aliasing (e.g., table as t)
                tbl = tbl.strip(',')
                if tbl and tbl not in tables:
                    tables.append(tbl)
            i += 1
        return tables

    def _extract_write_table(self, sql: str) -> Optional[str]:
        s = sql.strip().lower()
        try:
            if s.startswith('insert'):
                # INSERT INTO table
                parts = s.split()
                if 'into' in parts:
                    idx = parts.index('into')
                    if idx + 1 < len(parts):
                        tbl = parts[idx+1].strip('"`')
                        if '.' in tbl:
                            tbl = tbl.split('.')[-1]
                        return tbl
            if s.startswith('update'):
                parts = s.split()
                if len(parts) > 1:
                    tbl = parts[1].strip('"`')
                    if '.' in tbl:
                        tbl = tbl.split('.')[-1]
                    return tbl
            if s.startswith('delete'):
                # DELETE FROM table
                parts = s.split()
                if 'from' in parts:
                    idx = parts.index('from')
                    if idx + 1 < len(parts):
                        tbl = parts[idx+1].strip('"`')
                        if '.' in tbl:
                            tbl = tbl.split('.')[-1]
                        return tbl
        except Exception:
            return None
        return None
    
    async def _execute_rust_query(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a query using the Rust engine."""
        if not getattr(self, '_rust_engine', None):
            return {'success': False, 'error': 'Rust engine not initialized'}
        # Ensure connection only if not already connected
        try:
            if not self._rust_engine.is_connected():
                await self._rust_engine.connect()
                self.is_connected = True
                self._connected = True
        except Exception:
            # ignore if already connected
            pass
        try:
            result = await self._rust_engine.execute_query(sql, params or None)
            return result
        except Exception as e:
            msg = str(e)
            if 'Not connected' in msg:
                try:
                    await self._rust_engine.connect()
                    return await self._rust_engine.execute_query(sql, params or None)
                except Exception as e2:
                    return {'success': False, 'error': str(e2)}
            return {'success': False, 'error': msg}
    
    async def _execute_python_query(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Deprecated: Python DB I/O is disabled. Use Rust backend."""
        return {
            'success': False,
            'error': 'Python DB I/O disabled. Enable and build Rust backend (OXEN_RUST_BACKEND=1) to execute queries.',
            'data': [],
            'rows_affected': 0
        }
    
    async def execute_many(self, sql: str, params_list: List[List[Any]]) -> Dict[str, Any]:
        """Execute multiple queries with performance monitoring"""
        start_time = time_module.time()
        
        try:
            if not getattr(self, '_rust_engine', None) or not self.is_connected:
                await self.connect()
            result = await self._rust_engine.execute_many(sql, params_list)
            
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
        """Deprecated: kept for compatibility. Routes to Rust if possible."""
        if getattr(self, '_rust_engine', None):
            return await self._rust_engine.execute_many(sql, params_list)
        return {'success': False, 'error': 'Rust engine not initialized', 'sql': sql}
    
    @asynccontextmanager
    async def transaction(self):
        """Get a transaction context manager."""
        if not self._connected:
            raise ConnectionError("Not connected to database")
        if not getattr(self, '_rust_engine', None):
            raise ConnectionError("Rust engine not initialized. Ensure OXEN_RUST_BACKEND=1 and connect() was called.")
        
        transaction_id = None
        try:
            result = await self._rust_engine.begin_transaction()
            transaction_id = result.get("id")
            logger.info(f"Started Rust transaction: {transaction_id}")
            
            yield UnifiedTransaction(self, transaction_id)
            
            # Commit transaction
            await self._rust_engine.commit_transaction(transaction_id)
            logger.info(f"Committed transaction: {transaction_id}")
            
        except Exception as e:
            # Rollback transaction
            if transaction_id:
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
                if 'postgresql' in self.connection_string.lower():
                    # Pass native mapping for typed JSON binding in Rust
                    converted_values.append(value)
                else:
                    import json
                    converted_values.append(json.dumps(value))
            elif isinstance(value, list):  # Array field
                if 'postgresql' in self.connection_string.lower():
                    # Pass native list for typed array binding in Rust
                    converted_values.append(value)
                else:
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
        # Use RETURNING id when supported to retrieve PK directly
        conn_lower = self.connection_string.lower()
        supports_returning = ('postgresql' in conn_lower) or ('sqlite' in conn_lower)
        if supports_returning:
            sql = sql.strip() + " RETURNING id"
        
        result = await self.execute_query(sql, converted_values)
        # If we used RETURNING and got a row, propagate id
        if supports_returning and result.get('error') is None:
            rows = result.get('data') or []
            if isinstance(rows, list) and rows:
                first = rows[0]
                rid = None
                if isinstance(first, dict):
                    rid = first.get('id') or first.get('pk')
                elif isinstance(first, (list, tuple)) and first:
                    rid = first[0]
                if rid is not None:
                    result['data'] = {'id': int(rid)}
        # Try to fetch generated primary key id for convenience
        try:
            if result.get('error') is None:
                conn = self.connection_string.lower()
                existing_id = None
                d = result.get('data')
                if isinstance(d, dict):
                    existing_id = d.get('id')
                if 'sqlite' in conn and not existing_id:
                    sel = await self.execute_query("SELECT last_insert_rowid() AS id")
                    if sel.get('error') is None and sel.get('data'):
                        last_id = sel['data'][0].get('id')
                        if isinstance(last_id, (int, float)) and last_id:
                            if not isinstance(result.get('data'), dict):
                                result['data'] = {}
                            result['data']['id'] = int(last_id)
                elif 'mysql' in conn and not existing_id:
                    sel = await self.execute_query("SELECT LAST_INSERT_ID() AS id")
                    if sel.get('error') is None and sel.get('data'):
                        last_id = sel['data'][0].get('id')
                        if isinstance(last_id, (int, float)) and last_id:
                            if not isinstance(result.get('data'), dict):
                                result['data'] = {}
                            result['data']['id'] = int(last_id)
                elif 'postgresql' in conn and not existing_id:
                    # Best-effort: fetch latest id from table
                    qt = self._quote_identifier(table_name)
                    sel = await self.execute_query(f"SELECT id FROM {qt} ORDER BY id DESC LIMIT 1")
                    if sel.get('error') is None and sel.get('data'):
                        last_id = sel['data'][0].get('id')
                        if isinstance(last_id, (int, float)) and last_id:
                            if not isinstance(result.get('data'), dict):
                                result['data'] = {}
                            result['data']['id'] = int(last_id)
        except Exception:
            pass
        if 'data' not in result:
            result['data'] = {}
        return result
    
    async def insert_many(self, table_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert multiple records into a table using a single multi-row INSERT when possible."""
        if not records:
            return {"success": True, "rows_affected": 0, "data": {"ids": []}}

        columns = list(records[0].keys())

        # Convert values per record
        converted_records: List[List[Any]] = []
        for record in records:
            row: List[Any] = []
            for key in columns:
                value = record.get(key)
                if hasattr(value, 'as_tuple'):
                    if 'postgresql' in self.connection_string.lower():
                        row.append(float(value))
                    else:
                        row.append(str(value))
                elif isinstance(value, (datetime, date, time)):
                    if 'postgresql' in self.connection_string.lower():
                        row.append(value)
                    else:
                        row.append(str(value))
                elif isinstance(value, dict):
                    if 'postgresql' in self.connection_string.lower():
                        row.append(value)
                    else:
                        import json as _json
                        row.append(_json.dumps(value))
                elif isinstance(value, list):
                    if 'postgresql' in self.connection_string.lower():
                        row.append(value)
                    else:
                        import json as _json
                        row.append(_json.dumps(value))
                else:
                    row.append(value)
            converted_records.append(row)

        quoted_table = self._quote_identifier(table_name)
        quoted_columns = [self._quote_identifier(col) for col in columns]

        is_pg = 'postgresql' in self.connection_string.lower()
        is_sqlite = 'sqlite' in self.connection_string.lower()

        if is_pg:
            # Prefer COPY if enabled via env and Rust feature compiled
            if os.getenv('OXEN_PG_COPY', '0') == '1' and hasattr(self, '_rust_engine'):
                try:
                    rows_json = []
                    for row in converted_records:
                        rows_json.append({col: val for col, val in zip(columns, row)})
                    ir = {
                        'dialect': 'postgres',
                        'table': table_name,
                        'action': 'insert',
                        'rows': rows_json,
                    }
                    import json as _json
                    built = await self._rust_engine.execute_ir_json(_json.dumps(ir))  # type: ignore[attr-defined]
                    if isinstance(built, dict) and built.get('error') is None:
                        if 'data' not in built:
                            built['data'] = {'ids': []}
                        return built
                except Exception:
                    pass
            # Prefer Rust IR path for up to 500 rows to leverage chunking and potential RETURNING
            if hasattr(self, '_rust_engine') and len(converted_records) <= 500:
                try:
                    # Build IR for insert-many with RETURNING id
                    rows_json = []
                    for row in converted_records:
                        rows_json.append({col: val for col, val in zip(columns, row)})
                    ir = {
                        'dialect': 'postgres',
                        'table': table_name,
                        'action': 'insert',
                        'rows': rows_json,
                        'returning': ['id'],
                    }
                    import json as _json
                    built = await self._rust_engine.execute_ir_json(_json.dumps(ir))  # type: ignore[attr-defined]
                    # Normalize result
                    if isinstance(built, dict) and built.get('error') is None:
                        rows = built.get('data') or []
                        ids: List[int] = []
                        for r in rows:
                            rid = None
                            if isinstance(r, dict):
                                rid = r.get('id') or r.get('pk')
                            elif isinstance(r, (list, tuple)) and r:
                                rid = r[0]
                            if isinstance(rid, (int, float)):
                                ids.append(int(rid))
                        built['data'] = {'ids': ids}
                        return built
                except Exception:
                    pass
            # Fallback: Build a single multi-row INSERT ... VALUES (...), (...)
            values_clauses = []
            flat_params: List[Any] = []
            param_index = 1
            for row in converted_records:
                placeholders = [f"${i}" for i in range(param_index, param_index + len(columns))]
                values_clauses.append(f"({', '.join(placeholders)})")
                flat_params.extend(row)
                param_index += len(columns)
            sql = f"INSERT INTO {quoted_table} ({', '.join(quoted_columns)}) VALUES {', '.join(values_clauses)} RETURNING id"
            result = await self.execute_query(sql, flat_params)
            if result.get('error') is None:
                rows = result.get('data') or []
                ids: List[int] = []
                for r in rows:
                    if isinstance(r, dict):
                        rid = r.get('id') or r.get('pk')
                    elif isinstance(r, (list, tuple)):
                        rid = r[0] if r else None
                    else:
                        rid = None
                    if isinstance(rid, (int, float)):
                        ids.append(int(rid))
                result['data'] = {'ids': ids}
            return result
        elif is_sqlite:
            # SQLite supports multi-row VALUES with '?'
            values_clauses = []
            flat_params = []
            for row in converted_records:
                placeholders = ["?" for _ in row]
                values_clauses.append(f"({', '.join(placeholders)})")
                flat_params.extend(row)
            sql = f"INSERT INTO {quoted_table} ({', '.join(quoted_columns)}) VALUES {', '.join(values_clauses)}"
            result = await self.execute_query(sql, flat_params)
            # IDs retrieval omitted for SQLite batch; caller can refetch
            if 'data' not in result:
                result['data'] = {'ids': []}
            return result
        else:
            # MySQL: multi-row VALUES with '?' placeholders
            values_clauses = []
            flat_params = []
            for row in converted_records:
                placeholders = ["?" for _ in row]
                values_clauses.append(f"({', '.join(placeholders)})")
                flat_params.extend(row)
            sql = f"INSERT INTO {quoted_table} ({', '.join(quoted_columns)}) VALUES {', '.join(values_clauses)}"
            result = await self.execute_query(sql, flat_params)
            if 'data' not in result:
                result['data'] = {'ids': []}
            return result
    
    async def select_records(self, table_name: str, conditions: Optional[Dict[str, Any]] = None, 
                           limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """Select records from a table with optional conditions."""
        quoted_table = self._quote_identifier(table_name)
        sql = f'SELECT * FROM {quoted_table}'
        params = []
        
        if conditions:
            where_clauses = []
            if 'postgresql' in self.connection_string.lower():
                for key, value in conditions.items():
                    quoted_key = self._quote_identifier(key)
                    param_index = len(params) + 1
                    where_clauses.append(f'{quoted_key} = ${param_index}')
                    params.append(value)
            else:
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
    # Persist preference for Rust backend (env flag takes precedence)
    env_flag = os.getenv('OXEN_RUST_BACKEND', None)
    engine.use_rust = (env_flag != '0') if env_flag is not None else use_rust
    
    # Initialize Rust backend if available and requested
    if use_rust and RUST_AVAILABLE:
        try:
            from .rust_bridge import OxenEngine
            engine._rust_engine = OxenEngine(connection_string)
            engine.rust_engine = engine._rust_engine
            print(f"✅ Rust backend initialized for: {connection_string}")
        except Exception as e:
            print(f"⚠️  Failed to initialize Rust backend: {e}")
    
    return engine


# Global engine registry for multi-database support
_engines: Dict[str, UnifiedEngine] = {}
_last_engine: Optional[UnifiedEngine] = None


def register_engine(name: str, connection_string: str, use_rust: bool = True) -> UnifiedEngine:
    """Register a named engine."""
    engine = create_engine(connection_string, use_rust)
    _engines[name] = engine
    global _last_engine
    _last_engine = engine
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
    # Remember last engine for QuerySet fallback
    global _last_engine
    _last_engine = engine
    
    return engine


def get_default_engine() -> Optional[UnifiedEngine]:
    """Return the most recently created/connected engine if available."""
    return _last_engine


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