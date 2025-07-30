"""
Python bridge to the Rust backend for OxenORM
"""

import asyncio
from typing import Dict, List, Optional, Any

try:
    from oxen_engine import OxenEngine as RustOxenEngine
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print("Warning: Rust backend not available. Install with: cargo build")


class OxenEngine:
    """
    Python wrapper around the Rust OxenEngine with async interface
    """
    
    def __init__(self, connection_string: str):
        if not RUST_AVAILABLE:
            raise ImportError("Rust backend not available. Please build with: cargo build")
        
        self._rust_engine = RustOxenEngine(connection_string)
        self._connection_string = connection_string
    
    async def connect(self) -> Dict[str, Any]:
        """Connect to the database"""
        # Run the sync connect in a thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._rust_engine.connect)
        return result
    
    async def disconnect(self) -> None:
        """Disconnect from the database"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._rust_engine.close)
    
    async def execute_query(self, query: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a query and return results"""
        loop = asyncio.get_event_loop()
        if params:
            result = await loop.run_in_executor(None, self._rust_engine.execute_query, query, params)
        else:
            result = await loop.run_in_executor(None, self._rust_engine.execute_query, query)
        return result
    
    async def execute_many(self, query: str, params_list: List[List[Any]]) -> Dict[str, Any]:
        """Execute a query with multiple parameter sets"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._rust_engine.execute_many, query, params_list)
        return result
    
    async def insert_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single record into a table"""
        # Build INSERT query
        fields = list(data.keys())
        placeholders = ", ".join(["?" for _ in fields])
        field_names = ", ".join(fields)
        query = f"INSERT INTO {table_name} ({field_names}) VALUES ({placeholders})"
        
        # Execute insert
        result = await self.execute_query(query, list(data.values()))
        
        # Get the last inserted ID based on database type
        if result.get('error') is None:
            if 'sqlite' in self._connection_string.lower():
                # SQLite uses last_insert_rowid()
                last_id_result = await self.execute_query("SELECT last_insert_rowid() as id")
                if last_id_result.get('error') is None and last_id_result.get('data'):
                    last_id = last_id_result['data'][0].get('id')
                    if last_id and last_id != False and last_id != 0:
                        result['data'] = {'id': last_id}
                    else:
                        # Try alternative approach for SQLite too
                        if 'username' in data:
                            select_result = await self.execute_query(
                                f"SELECT id FROM {table_name} WHERE username = ? ORDER BY id DESC LIMIT 1",
                                [data['username']]
                            )
                            if select_result.get('error') is None and select_result.get('data'):
                                alt_id = select_result['data'][0].get('id')
                                if alt_id and alt_id != False and alt_id != 0:
                                    result['data'] = {'id': alt_id}
            elif 'mysql' in self._connection_string.lower():
                # MySQL uses LAST_INSERT_ID()
                last_id_result = await self.execute_query("SELECT LAST_INSERT_ID() as id")
                if last_id_result.get('error') is None and last_id_result.get('data'):
                    last_id = last_id_result['data'][0].get('id')
                    # Check if the ID is valid (not False, not 0, not None)
                    if last_id and last_id != False and last_id != 0 and last_id is not None:
                        result['data'] = {'id': last_id}
                    else:
                        # Try alternative approach - query the actual inserted record
                        if 'username' in data:
                            # Try to get the ID by querying the inserted record
                            select_result = await self.execute_query(
                                f"SELECT id FROM {table_name} WHERE username = ? ORDER BY id DESC LIMIT 1",
                                [data['username']]
                            )
                            if select_result.get('error') is None and select_result.get('data'):
                                alt_id = select_result['data'][0].get('id')
                                if alt_id and alt_id != False and alt_id != 0:
                                    result['data'] = {'id': alt_id}
                else:
                    print(f"DEBUG: MySQL LAST_INSERT_ID failed: {last_id_result}")
        
        return result
    
    async def insert_many(self, table_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert multiple records into a table"""
        if not records:
            return {"success": True, "data": {"ids": []}}
        
        # Build INSERT query
        fields = list(records[0].keys())
        placeholders = ", ".join(["?" for _ in fields])
        field_names = ", ".join(fields)
        query = f"INSERT INTO {table_name} ({field_names}) VALUES ({placeholders})"
        
        # Prepare parameters
        params_list = [list(record.values()) for record in records]
        
        # Execute bulk insert
        result = await self.execute_many(query, params_list)
        return result
    
    async def update_records(self, table_name: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Update records in a table"""
        # Build UPDATE query
        set_clause = ", ".join([f"{field} = ?" for field in data.keys()])
        where_clause = " AND ".join([f"{field} = ?" for field in conditions.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        
        # Prepare parameters
        params = list(data.values()) + list(conditions.values())
        
        # Execute update
        result = await self.execute_query(query, params)
        return result
    
    async def delete_records(self, table_name: str, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Delete records from a table"""
        # Build DELETE query
        where_clause = " AND ".join([f"{field} = ?" for field in conditions.keys()])
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        
        # Execute delete
        result = await self.execute_query(query, list(conditions.values()))
        return result
    
    async def select_records(self, table_name: str, conditions: Optional[Dict[str, Any]] = None, 
                           limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        """Select records from a table"""
        # Build SELECT query
        query = f"SELECT * FROM {table_name}"
        params = []
        
        if conditions:
            where_clause = " AND ".join([f"{field} = ?" for field in conditions.keys()])
            query += f" WHERE {where_clause}"
            params = list(conditions.values())
        
        if limit:
            query += f" LIMIT {limit}"
        
        if offset:
            query += f" OFFSET {offset}"
        
        # Execute select
        result = await self.execute_query(query, params if params else None)
        return result
    
    async def count_records(self, table_name: str, conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Count records in a table"""
        # Build COUNT query
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        params = []
        
        if conditions:
            where_clause = " AND ".join([f"{field} = ?" for field in conditions.keys()])
            query += f" WHERE {where_clause}"
            params = list(conditions.values())
        
        # Execute count
        result = await self.execute_query(query, params if params else None)
        return result
    
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> Dict[str, Any]:
        """Create a table with the given schema"""
        # Build CREATE TABLE query
        columns = []
        for field_name, field_type in schema.items():
            columns.append(f"{field_name} {field_type}")
        
        columns_clause = ", ".join(columns)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_clause})"
        
        # Execute create table
        result = await self.execute_query(query)
        return result
    
    async def drop_table(self, table_name: str) -> Dict[str, Any]:
        """Drop a table"""
        query = f"DROP TABLE IF EXISTS {table_name}"
        result = await self.execute_query(query)
        return result
    
    async def begin_transaction(self):
        """Begin a transaction"""
        return OxenTransaction(self)
    
    def transaction(self):
        """Create a transaction context manager."""
        return TransactionContext(self._rust_engine)

    def close(self):
        """Close the connection (synchronous wrapper)"""
        return self._rust_engine.close()


class OxenTransaction:
    """Transaction wrapper for OxenEngine"""
    
    def __init__(self, engine: OxenEngine):
        self.engine = engine
        self._transaction_id = None
    
    async def commit(self) -> None:
        """Commit the transaction"""
        await self.engine.execute_query("COMMIT")
    
    async def rollback(self) -> None:
        """Rollback the transaction"""
        await self.engine.execute_query("ROLLBACK")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.engine.execute_query("BEGIN TRANSACTION")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback() 


class TransactionContext:
    """Transaction context manager."""
    
    def __init__(self, rust_engine):
        self.rust_engine = rust_engine
        self._in_transaction = False
    
    async def __aenter__(self):
        """Start a transaction."""
        # Begin transaction - use different syntax for MySQL vs SQLite
        if hasattr(self.rust_engine, '_connection_string') and 'mysql' in self.rust_engine._connection_string.lower():
            # MySQL uses START TRANSACTION
            result = await self.rust_engine.execute_query("START TRANSACTION")
        else:
            # SQLite uses BEGIN TRANSACTION
            result = await self.rust_engine.execute_query("BEGIN TRANSACTION")
        
        if result.get('error') is None:
            self._in_transaction = True
            return self
        else:
            raise OperationalError(f"Failed to begin transaction: {result.get('error')}")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End a transaction."""
        if self._in_transaction:
            if exc_type is None:
                # Commit transaction
                result = await self.rust_engine.execute_query("COMMIT")
                if result.get('error') is not None:
                    raise OperationalError(f"Failed to commit transaction: {result.get('error')}")
            else:
                # Rollback transaction
                result = await self.rust_engine.execute_query("ROLLBACK")
                if result.get('error') is not None:
                    raise OperationalError(f"Failed to rollback transaction: {result.get('error')}")
            self._in_transaction = False 