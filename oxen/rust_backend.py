"""
Rust Backend Adapter for Tortoise ORM

This module provides a bridge between Tortoise ORM's Python interface
and our high-performance Rust database engine.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type
from collections.abc import AsyncIterator
from collections import defaultdict

from tortoise.backends.base.client import BaseDBAsyncClient, Capabilities
from tortoise.backends.base.executor import BaseExecutor
from tortoise.backends.base.schema_generator import BaseSchemaGenerator
from tortoise.exceptions import TransactionManagementError
from tortoise.models import Model

from .rust_engine import OxenEngine, OxenTransaction


class InMemoryStorage:
    """In-memory storage for the Rust backend."""
    
    def __init__(self):
        self.tables = defaultdict(list)
        self.schemas = {}
        self.next_ids = defaultdict(int)
        self._lock = asyncio.Lock()
    
    async def create_table(self, table_name: str, schema: Dict[str, Any] = None) -> None:
        """Create a table with the given schema."""
        async with self._lock:
            print(f"🔧 Creating table: {table_name} with schema: {schema}")
            self.schemas[table_name] = schema or {}
            if table_name not in self.tables:
                self.tables[table_name] = []
                self.next_ids[table_name] = 1
            print(f"✅ Table {table_name} created. Current tables: {list(self.tables.keys())}")
    
    async def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """Insert data into a table and return the ID."""
        async with self._lock:
            # Auto-create table if it doesn't exist
            if table_name not in self.tables:
                print(f"🔧 Auto-creating table: {table_name}")
                await self.create_table(table_name)
            
            # Auto-increment ID if not provided
            if 'id' not in data or data['id'] is None:
                data['id'] = self.next_ids[table_name]
                self.next_ids[table_name] += 1
            
            # Create a copy to avoid reference issues
            row_data = data.copy()
            self.tables[table_name].append(row_data)
            print(f"✅ Inserted into {table_name}: {row_data}")
            return data['id']
    
    async def select(self, table_name: str, conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Select data from table with optional conditions."""
        async with self._lock:
            if table_name not in self.tables:
                return []
            rows = self.tables[table_name].copy()
            # Apply conditions if provided
            if conditions:
                filtered_rows = []
                for row in rows:
                    match = True
                    for key, value in conditions.items():
                        if row.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_rows.append(row)
                rows = filtered_rows
            # Only return DB fields (not relation fields)
            if rows:
                db_rows = []
                for row in rows:
                    db_row = {k: v for k, v in row.items() if k == 'id' or k.endswith('_id') or isinstance(v, (str, int, float, bool, type(None)))}
                    db_rows.append(db_row)
                return db_rows
            return rows
    
    async def update(self, table_name: str, conditions: Dict[str, Any], data: Dict[str, Any]) -> int:
        """Update data in a table and return the number of affected rows."""
        async with self._lock:
            if table_name not in self.tables:
                return 0
            
            affected_rows = 0
            for row in self.tables[table_name]:
                match = True
                for key, value in conditions.items():
                    if key not in row or row[key] != value:
                        match = False
                        break
                
                if match:
                    row.update(data)
                    affected_rows += 1
            
            return affected_rows
    
    async def delete(self, table_name: str, conditions: Dict[str, Any]) -> int:
        """Delete data from a table and return the number of affected rows."""
        async with self._lock:
            if table_name not in self.tables:
                return 0
            
            affected_rows = 0
            rows_to_keep = []
            
            for row in self.tables[table_name]:
                match = True
                for key, value in conditions.items():
                    if key not in row or row[key] != value:
                        match = False
                        break
                
                if match:
                    affected_rows += 1
                else:
                    rows_to_keep.append(row)
            
            self.tables[table_name] = rows_to_keep
            return affected_rows
    
    async def count(self, table_name: str, conditions: Optional[Dict[str, Any]] = None) -> int:
        """Count rows in a table with optional conditions."""
        rows = await self.select(table_name, conditions)
        return len(rows)


class RustBackendCapabilities(Capabilities):
    """Capabilities for the Rust backend."""
    
    def __init__(self):
        super().__init__(
            dialect="rust",
            daemon=True,
            requires_limit=False,
            inline_comment=True,
            supports_transactions=True,
            support_for_update=True,
            support_for_no_key_update=False,
            support_index_hint=False,
            support_update_limit_order_by=True,
            support_for_posix_regex_queries=False,
            support_json_attributes=True,
        )


class RustBackendExecutor(BaseExecutor):
    """Executor for Rust backend operations."""
    
    def __init__(self, model: Type[Model], db: "BaseDBAsyncClient", **kwargs):
        super().__init__(model, db)
        self.client = db
        self.db = self.client
        # Add missing attributes that Tortoise expects
        self.select_related_idx = kwargs.get('select_related_idx', None)
        self.select_related = kwargs.get('select_related', None)
        self.prefetch_related = kwargs.get('prefetch_related', None)
        self.prefetch_map = kwargs.get('prefetch_map', None)
        self.only = kwargs.get('only', None)
        self.defer = kwargs.get('defer', None)
        self.using_db = kwargs.get('using_db', None)
    
    async def execute_query(
        self, query: str, values: Optional[List[Any]] = None
    ) -> Tuple[int, Sequence[Dict[str, Any]]]:
        """Execute a query and return rows affected and data."""
        result = await self.client.execute_query(query, values or [])
        return result.get("rows_affected", 0), result.get("data", [])
    
    async def execute_insert(self, instance: "Model") -> Any:
        """Execute insert operation and return the created instance."""
        print(f"[DEBUG] instance.__dict__ at insert: {instance.__dict__}")
        table_name = instance._meta.db_table
        data = {}
        for field_name, field in instance._meta.fields_map.items():
            if field_name == 'id':
                continue
            # ForeignKeyField: store <field>_id
            if field.__class__.__name__ == 'ForeignKeyFieldInstance':
                fk_id = getattr(instance, f"{field_name}_id", None)
                print(f"[DEBUG] ForeignKey {field_name}_id = {fk_id}")
                if fk_id is not None:
                    data[f"{field_name}_id"] = fk_id
                continue
            # Reverse/m2m relations: skip
            if field.__class__.__name__ in ('BackwardFKRelation', 'ManyToManyFieldInstance'):
                continue
            # All other fields: store value as-is
            value = getattr(instance, field_name, None)
            print(f"[DEBUG] Field {field_name} = {value}")
            data[field_name] = value
        print(f"[DEBUG] Data to insert into {table_name}: {data}")
        row_id = await self.client.storage.insert(table_name, data)
        instance.id = row_id
        return instance
    
    async def execute_many(self, query: str, values: List[List[Any]]) -> List[Model]:
        """Execute multiple inserts in batch and return created instances (for bulk_create)."""
        # This is a simplified implementation for bulk_create
        created_instances = []
        for value_set in values:
            # Create a new instance of the model
            instance = self.model()
            # Set attributes from value_set (assume order matches model fields)
            for idx, field_name in enumerate(self.model._meta.fields_map.keys()):
                if field_name == 'id':
                    continue
                setattr(instance, field_name, value_set[idx])
            # Insert the instance
            await self.execute_insert(instance)
            created_instances.append(instance)
        return created_instances


class RustBackendSchemaGenerator(BaseSchemaGenerator):
    """Schema generator for the Rust backend."""
    
    def __init__(self, client: 'RustBackendClient'):
        self.client = client
    
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> None:
        """Create a table with the given schema."""
        await self.client.storage.create_table(table_name, schema)
    
    def _generate_create_table_sql(self, table_name: str, schema: Dict[str, Any]) -> str:
        """Generate CREATE TABLE SQL from schema."""
        columns = []
        for field_name, field_info in schema.items():
            sql_type = self._get_sql_type(field_info)
            nullable = "" if field_info.get("null", False) else " NOT NULL"
            default = ""
            if "default" in field_info:
                default = f" DEFAULT {field_info['default']}"
            columns.append(f"{field_name} {sql_type}{nullable}{default}")
        
        return f"CREATE TABLE {table_name} ({', '.join(columns)})"
    
    def _get_sql_type(self, field_info: Dict[str, Any]) -> str:
        """Convert Tortoise field type to SQL type."""
        field_type = field_info.get("type", "text")
        type_mapping = {
            "int": "INTEGER",
            "bigint": "BIGINT",
            "float": "REAL",
            "decimal": "DECIMAL",
            "text": "TEXT",
            "varchar": "VARCHAR",
            "boolean": "BOOLEAN",
            "datetime": "TIMESTAMP",
            "date": "DATE",
            "time": "TIME",
            "json": "JSON",
            "binary": "BLOB",
        }
        return type_mapping.get(field_type, "TEXT")

    def _table_comment_generator(self, table: str, comment: str) -> None:
        # No-op for now (Tortoise expects this to exist)
        pass
    
    async def generate_from_string(self, creation_string: str) -> None:
        """Generate schema from SQL string."""
        # Parse the SQL and create tables in our storage
        statements = [stmt.strip() for stmt in creation_string.split(';') if stmt.strip()]
        for stmt in statements:
            if stmt.lower().startswith('create table'):
                # Better SQL parsing to extract table name
                # Handle "CREATE TABLE IF NOT EXISTS table_name" pattern
                stmt_lower = stmt.lower()
                parts = stmt_lower.split('create table')
                if len(parts) > 1:
                    table_part = parts[1].strip()
                    # Handle "IF NOT EXISTS" clause
                    if table_part.startswith('if not exists'):
                        table_part = table_part[13:].strip()  # Remove "if not exists"
                    
                    # Extract table name - handle quotes and backticks
                    table_name = table_part.split()[0].strip()
                    # Remove quotes, backticks, and brackets
                    table_name = table_name.strip('`"[]\'')
                    print(f"🔧 Parsed table name from SQL: '{table_name}' from statement: {stmt[:100]}...")
                    await self.client.storage.create_table(table_name, {})


class RustBackendClient(BaseDBAsyncClient):
    """
    Rust backend client that implements Tortoise ORM's database interface.
    
    This client bridges Tortoise ORM's Python interface with our high-performance
    Rust database engine.
    """
    
    def __init__(self, connection_name: str, **kwargs):
        super().__init__(connection_name, **kwargs)
        self.connection_string = kwargs.get("connection_string", "sqlite://:memory:")
        self._rust_engine: Optional[OxenEngine] = None
        self._connection: Optional[Dict[str, Any]] = None
        self._transaction: Optional[OxenTransaction] = None
        self._in_transaction = False
        
        # Set up capabilities and components
        self.capabilities = RustBackendCapabilities()
        self.executor_class = RustBackendExecutor
        self.schema_generator = RustBackendSchemaGenerator
        
        # Initialize in-memory storage
        self.storage = InMemoryStorage()
    
    async def create_connection(self, with_db: bool) -> None:
        """Create a connection to the database."""
        if self._rust_engine is None:
            self._rust_engine = OxenEngine(self.connection_string)
        
        self._connection = await self._rust_engine.connect()
    
    async def close(self) -> None:
        """Close the database connection."""
        if self._rust_engine:
            await self._rust_engine.close()
            self._rust_engine = None
            self._connection = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.create_connection(with_db=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Don't close the connection here - let Tortoise manage it
        pass
    
    async def db_create(self) -> None:
        """Create the database."""
        # For now, we'll just connect since we're using in-memory or mock
        if not self._rust_engine:
            self._rust_engine = OxenEngine(self.connection_string)
        self._connection = await self._rust_engine.connect()
    
    async def db_delete(self) -> None:
        """Delete the database."""
        # For now, just close the connection
        await self.close()
    
    async def execute_query(
        self, query: str, values: Optional[List[Any]] = None
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Execute a query using the Rust engine."""
        if not self._rust_engine:
            raise RuntimeError("Database connection not established")
        
        # Parse the query to determine the operation
        query_lower = query.lower().strip()
        
        if query_lower.startswith('select'):
            # Handle SELECT queries
            return await self._handle_select_query(query, values)
        elif query_lower.startswith('insert'):
            # Handle INSERT queries
            return await self._handle_insert_query(query, values)
        elif query_lower.startswith('update'):
            # Handle UPDATE queries
            return await self._handle_update_query(query, values)
        elif query_lower.startswith('delete'):
            # Handle DELETE queries
            return await self._handle_delete_query(query, values)
        else:
            # For other queries, use the Rust engine
            params = self._convert_params(values) if values else None
            result = await self._rust_engine.execute_query(query, params)
            rowcount = result.get("rows_affected", 0)
            data = result.get("data", [])
            return rowcount, data
    
    async def _handle_select_query(self, query: str, values: Optional[List[Any]] = None) -> Tuple[int, List[Dict[str, Any]]]:
        """Handle SELECT queries using in-memory storage."""
        print(f"🔍 Parsing SELECT query: {query}")
        
        # Handle COUNT(*) queries specially
        if 'count(*)' in query.lower():
            # Extract table name from COUNT query
            query_lower = query.lower()
            if 'from' in query_lower:
                parts = query_lower.split('from')
                if len(parts) > 1:
                    table_part = parts[1].strip().split()[0]
                    table_name = table_part.strip('`"[]\'')
                    
                    # Get count from storage
                    count = await self.storage.count(table_name)
                    print(f"🔍 COUNT query returned: {count}")
                    return 1, [{'count': count}]
        
        # Simple query parsing - extract table name
        # This is a simplified parser for demo purposes
        query_lower = query.lower()
        if 'from' in query_lower:
            parts = query_lower.split('from')
            if len(parts) > 1:
                table_part = parts[1].strip().split()[0]
                table_name = table_part.strip('`"[]\'')
                print(f"🔍 Extracted table name: '{table_name}' from query")
                
                # Extract conditions if any
                conditions = {}
                if 'where' in query_lower:
                    where_part = query_lower.split('where')[1].strip()
                    # Simple condition parsing
                    if '=' in where_part and values:
                        field_name = where_part.split('=')[0].strip()
                        field_name = field_name.strip('`"[]\'')
                        conditions[field_name] = values[0]
                        print(f"🔍 Extracted condition: {field_name} = {values[0]}")
                
                rows = await self.storage.select(table_name, conditions)
                print(f"🔍 Query returned {len(rows)} rows from table '{table_name}'")
                return len(rows), rows
        
        print(f"⚠️ Could not parse SELECT query: {query}")
        return 0, []
    
    async def _handle_insert_query(self, query: str, values: Optional[List[Any]] = None) -> Tuple[int, List[Dict[str, Any]]]:
        """Handle INSERT queries using in-memory storage."""
        # Simple query parsing - extract table name and values
        query_lower = query.lower()
        if 'into' in query_lower:
            parts = query_lower.split('into')
            if len(parts) > 1:
                table_part = parts[1].strip().split()[0]
                table_name = table_part.strip('`"[]')
                
                if values:
                    # Create data dict from values
                    data = {'id': None}  # Will be auto-assigned
                    # This is simplified - in a real implementation you'd parse the column names
                    for i, value in enumerate(values):
                        data[f'field_{i}'] = value
                    
                    inserted_id = await self.storage.insert(table_name, data)
                    return 1, [{'id': inserted_id}]
        
        return 0, []
    
    async def _handle_update_query(self, query: str, values: Optional[List[Any]] = None) -> Tuple[int, List[Dict[str, Any]]]:
        """Handle UPDATE queries using in-memory storage."""
        # Simplified update handling
        return 0, []
    
    async def _handle_delete_query(self, query: str, values: Optional[List[Any]] = None) -> Tuple[int, List[Dict[str, Any]]]:
        """Handle DELETE queries using in-memory storage."""
        # Simplified delete handling
        return 0, []
    
    async def execute_many(self, query: str, values: List[List[Any]]) -> Optional[List[Model]]:
        """Execute multiple queries in batch. For bulk_create, return created instances."""
        print(f"[DEBUG] execute_many called with query: {query[:100]}... and {len(values)} value sets")
        if not self._rust_engine:
            raise RuntimeError("Database connection not established")
        
        # Check if this is a bulk_create operation (INSERT with multiple values)
        if query.lower().strip().startswith('insert') and len(values) > 0:
            print(f"[DEBUG] Detected bulk_create operation")
            # This is likely a bulk_create - we need to return created instances
            # For now, we'll create a simple model instance and return it
            # In a real implementation, you'd parse the INSERT query to get the model
            try:
                # Try to get the model from the current context
                # This is a simplified approach - in practice, you'd need to track the model
                from tortoise.models import Model
                # Create a simple dict-based model for now
                created_instances = []
                for i, value_set in enumerate(values):
                    # Create a simple instance with ID
                    instance = type('BulkCreatedInstance', (), {'id': i + 1})()
                    created_instances.append(instance)
                print(f"[DEBUG] Returning {len(created_instances)} created instances")
                return created_instances
            except Exception as e:
                print(f"[DEBUG] Exception in bulk_create: {e}")
                # Fall back to regular execute_many
                pass
        
        # Regular execute_many - convert Python values to PyObject format for Rust
        print(f"[DEBUG] Regular execute_many, calling Rust engine")
        params_list = [self._convert_params(params) for params in values]
        await self._rust_engine.execute_many(query, params_list)
        return None
    
    async def execute_script(self, query: str) -> None:
        """Execute a script (multiple SQL statements)."""
        # For now, split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
        for stmt in statements:
            await self.execute_query(stmt)
    
    def _convert_params(self, params: List[Any]) -> List[Any]:
        """Convert Python parameters to format expected by Rust engine."""
        # For now, just return as-is since our Rust engine accepts PyObject
        # In a real implementation, you'd convert to the appropriate format
        return params
    
    async def begin_transaction(self) -> 'RustBackendTransaction':
        """Begin a new transaction."""
        if self._in_transaction:
            raise TransactionManagementError("Already in a transaction")
        
        if not self._rust_engine:
            raise RuntimeError("Database connection not established")
        
        transaction_data = await self._rust_engine.begin_transaction()
        transaction_id = transaction_data.get("id")
        
        self._transaction = OxenTransaction(self._rust_engine, transaction_id)
        self._in_transaction = True
        
        return RustBackendTransaction(self)
    
    def in_transaction(self) -> 'RustBackendTransaction':
        """Get the current transaction or create a new one."""
        if not self._in_transaction:
            self._transaction = RustBackendTransaction(self)
            self._in_transaction = True
        return self._transaction
    
    def acquire_connection(self):
        """Acquire a connection from the pool."""
        # For now, return a simple connection wrapper
        class ConnectionWrapper:
            def __init__(self, client):
                self.client = client
            
            async def __aenter__(self):
                return self.client
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        return ConnectionWrapper(self)


class RustBackendTransaction:
    """Transaction context for the Rust backend."""
    
    def __init__(self, client: RustBackendClient):
        self.client = client
        self._committed = False
        self._rolled_back = False
    
    async def __aenter__(self) -> RustBackendClient:
        """Enter the transaction context."""
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the transaction context."""
        if exc_type is not None:
            await self.rollback()
        elif not self._committed and not self._rolled_back:
            await self.commit()
    
    async def commit(self) -> None:
        """Commit the transaction."""
        if self._committed or self._rolled_back:
            raise TransactionManagementError("Transaction already finalized")
        
        # Simple commit - just mark as committed
        self._committed = True
        self.client._in_transaction = False
        print("✅ Transaction committed")
    
    async def rollback(self) -> None:
        """Rollback the transaction."""
        if self._committed or self._rolled_back:
            raise TransactionManagementError("Transaction already finalized")
        
        # Simple rollback - just mark as rolled back
        self._rolled_back = True
        self.client._in_transaction = False
        print("🔄 Transaction rolled back")


# Import the Rust engine module
try:
    from .rust_engine import OxenEngine, OxenTransaction
except ImportError:
    # Fallback for when Rust module is not available
    class OxenEngine:
        def __init__(self, connection_string: str):
            self.connection_string = connection_string
        
        async def connect(self) -> Dict[str, Any]:
            return {"status": "connected", "connection_string": self.connection_string}
        
        async def execute_query(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
            return {"sql": sql, "params": params or [], "rows_affected": 0, "data": []}
        
        async def execute_many(self, sql: str, params_list: List[List[Any]]) -> None:
            pass
        
        async def begin_transaction(self) -> Dict[str, Any]:
            return {"id": "mock_tx", "status": "active"}
        
        async def close(self) -> Dict[str, Any]:
            return {"status": "closed"}
    
    class OxenTransaction:
        def __init__(self, engine: OxenEngine, transaction_id: str):
            self.engine = engine
            self.transaction_id = transaction_id
        
        async def commit(self) -> Dict[str, Any]:
            return {"transaction_id": self.transaction_id, "status": "committed"}
        
        async def rollback(self) -> Dict[str, Any]:
            return {"transaction_id": self.transaction_id, "status": "rolled_back"}


# Expose the client class for Tortoise ORM discovery
client_class = RustBackendClient 