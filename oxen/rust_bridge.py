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
    Python wrapper around the Rust OxenEngine
    """
    
    def __init__(self, connection_string: str):
        if not RUST_AVAILABLE:
            raise ImportError("Rust backend not available. Please build with: cargo build")
        
        self._rust_engine = RustOxenEngine(connection_string)
    
    async def connect(self) -> None:
        """Connect to the database"""
        await self._rust_engine.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from the database"""
        await self._rust_engine.disconnect()
    
    async def insert_model(
        self,
        table_name: str,
        data: Dict[str, Any],
        pk_field: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """Insert a model into the database"""
        return await self._rust_engine.insert_model(table_name, data, pk_field)
    
    async def update_model(
        self,
        table_name: str,
        pk_value: Any,
        data: Dict[str, Any],
        pk_field: str = "id"
    ) -> bool:
        """Update a model in the database"""
        return await self._rust_engine.update_model(table_name, pk_value, data, pk_field)
    
    async def delete_model(
        self,
        table_name: str,
        pk_value: Any,
        pk_field: str = "id"
    ) -> bool:
        """Delete a model from the database"""
        return await self._rust_engine.delete_model(table_name, pk_value, pk_field)
    
    async def get_model(
        self,
        table_name: str,
        conditions: Dict[str, Any],
        pk_field: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """Get a single model from the database"""
        return await self._rust_engine.get_model(table_name, conditions, pk_field)
    
    async def query_models(
        self,
        table_name: str,
        conditions: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: List[str] = None,
        pk_field: str = "id"
    ) -> List[Dict[str, Any]]:
        """Query multiple models from the database"""
        if order_by is None:
            order_by = []
        return await self._rust_engine.query_models(
            table_name, conditions, limit, offset, order_by, pk_field
        )
    
    async def count_models(
        self,
        table_name: str,
        conditions: Dict[str, Any]
    ) -> int:
        """Count models matching conditions"""
        return await self._rust_engine.count_models(table_name, conditions)
    
    async def bulk_insert(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        pk_field: str = "id"
    ) -> List[Dict[str, Any]]:
        """Bulk insert multiple models"""
        return await self._rust_engine.bulk_insert(table_name, records, pk_field)
    
    async def bulk_update(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        pk_field: str = "id"
    ) -> int:
        """Bulk update multiple models"""
        return await self._rust_engine.bulk_update(table_name, records, pk_field)
    
    async def execute_raw_sql(
        self,
        sql: str,
        params: List[Any]
    ) -> List[Dict[str, Any]]:
        """Execute raw SQL query"""
        return await self._rust_engine.execute_raw_sql(sql, params)
    
    async def create_table(
        self,
        table_name: str,
        schema: Dict[str, str]
    ) -> None:
        """Create a new table"""
        await self._rust_engine.create_table(table_name, schema)
    
    async def drop_table(self, table_name: str) -> None:
        """Drop a table"""
        await self._rust_engine.drop_table(table_name)
    
    async def begin_transaction(self):
        """Begin a new transaction"""
        await self._rust_engine.begin_transaction()
        return OxenTransaction()


class OxenTransaction:
    """
    Python wrapper around the Rust OxenTransaction
    """
    
    def __init__(self):
        if not RUST_AVAILABLE:
            raise ImportError("Rust backend not available. Please build with: cargo build")
    
    async def commit(self) -> None:
        """Commit the transaction"""
        # TODO: Implement when Rust transaction is ready
        pass
    
    async def rollback(self) -> None:
        """Rollback the transaction"""
        # TODO: Implement when Rust transaction is ready
        pass 