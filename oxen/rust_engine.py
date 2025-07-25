"""
Python wrapper for the Rust OxenEngine module.

This module provides a clean Python interface to the Rust database engine.
"""

import asyncio
from typing import Any, Dict, List, Optional

try:
    from oxen_engine import OxenEngine as RustOxenEngine, OxenTransaction as RustOxenTransaction
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


class OxenEngine:
    """
    Python wrapper for the Rust OxenEngine.
    
    This class provides a clean async interface to the Rust database engine,
    handling the conversion between Python and Rust types.
    """
    
    def __init__(self, connection_string: str):
        if not RUST_AVAILABLE:
            raise ImportError("Rust engine not available. Please build the Rust module first.")
        
        self._rust_engine = RustOxenEngine(connection_string)
        self.connection_string = connection_string
    
    def configure_pool(self, max_connections: Optional[int] = None, min_connections: Optional[int] = None):
        """Configure the connection pool settings."""
        self._rust_engine.configure_pool(max_connections, min_connections)
    
    def is_connected(self) -> bool:
        """Check if connected to the database."""
        return self._rust_engine.is_connected()
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get the connection pool status."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        return self._rust_engine.get_pool_status()
    
    async def connect(self) -> Dict[str, Any]:
        """Connect to the database."""
        # Since our Rust methods are not async, we'll simulate async behavior
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        # Call the Rust method directly
        result = self._rust_engine.connect()
        return result
    
    async def execute_query(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a query with optional parameters."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        # Convert Python parameters to the format expected by Rust
        rust_params = self._convert_to_rust_params(params) if params else None
        
        # Execute the query
        result = self._rust_engine.execute_query(sql, rust_params)
        return result
    
    async def execute_many(self, sql: str, params_list: List[List[Any]]) -> None:
        """Execute multiple queries in batch."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        # Convert Python parameters to the format expected by Rust
        rust_params_list = [self._convert_to_rust_params(params) for params in params_list]
        
        # Execute the batch
        self._rust_engine.execute_many(sql, rust_params_list)
    
    async def begin_transaction(self) -> Dict[str, Any]:
        """Begin a new transaction."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        result = self._rust_engine.begin_transaction()
        return result
    
    async def commit_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Commit a transaction."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        result = self._rust_engine.commit_transaction(transaction_id)
        return result
    
    async def rollback_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Rollback a transaction."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        result = self._rust_engine.rollback_transaction(transaction_id)
        return result
    
    async def close(self) -> Dict[str, Any]:
        """Close the database connection."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        result = self._rust_engine.close()
        return result
    
    def _convert_to_rust_params(self, params: List[Any]) -> List[Any]:
        """
        Convert Python parameters to the format expected by the Rust engine.
        
        This method handles the conversion of Python types to PyObject format
        that can be passed to the Rust engine.
        """
        # For now, we pass parameters as-is since our Rust engine accepts PyObject
        # In a more sophisticated implementation, you might need to convert
        # specific Python types to Rust-compatible formats
        return params


class OxenTransaction:
    """
    Python wrapper for the Rust OxenTransaction.
    
    This class provides a clean async interface to Rust transactions.
    """
    
    def __init__(self, engine: OxenEngine, transaction_id: str):
        if not RUST_AVAILABLE:
            raise ImportError("Rust engine not available. Please build the Rust module first.")
        
        self._rust_transaction = RustOxenTransaction(engine._rust_engine, transaction_id)
        self.engine = engine
        self.transaction_id = transaction_id
    
    async def commit(self) -> Dict[str, Any]:
        """Commit the transaction."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        result = self._rust_transaction.commit()
        return result
    
    async def rollback(self) -> Dict[str, Any]:
        """Rollback the transaction."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        result = self._rust_transaction.rollback()
        return result
    
    async def execute(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Execute a query within the transaction."""
        await asyncio.sleep(0.001)  # Small delay to make it async
        
        # Convert Python parameters to the format expected by Rust
        rust_params = self.engine._convert_to_rust_params(params) if params else None
        
        # Execute the query
        result = self._rust_transaction.execute(sql, rust_params)
        return result


# Fallback implementation when Rust is not available
if not RUST_AVAILABLE:
    class MockOxenEngine:
        """Mock implementation when Rust engine is not available."""
        
        def __init__(self, connection_string: str):
            self.connection_string = connection_string
        
        def configure_pool(self, max_connections: Optional[int] = None, min_connections: Optional[int] = None):
            """Configure the connection pool settings (mock)."""
            pass
        
        def is_connected(self) -> bool:
            """Check if connected to the database (mock)."""
            return False
        
        async def get_pool_status(self) -> Dict[str, Any]:
            """Get the connection pool status (mock)."""
            await asyncio.sleep(0.001)
            return {
                "pool_size": 0,
                "idle_connections": 0,
                "used_connections": 0,
                "max_connections": 0,
                "min_connections": 0,
                "note": "Mock pool status - Rust engine not available"
            }
        
        async def connect(self) -> Dict[str, Any]:
            await asyncio.sleep(0.01)  # Simulate async operation
            return {
                "status": "connected",
                "connection_string": self.connection_string,
                "note": "Using mock implementation - Rust engine not available"
            }
        
        async def execute_query(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
            await asyncio.sleep(0.005)  # Simulate async operation
            return {
                "sql": sql,
                "params": params or [],
                "rows_affected": 0,
                "data": [],
                "note": "Mock execution - Rust engine not available"
            }
        
        async def execute_many(self, sql: str, params_list: List[List[Any]]) -> None:
            await asyncio.sleep(0.01)  # Simulate async operation
        
        async def begin_transaction(self) -> Dict[str, Any]:
            await asyncio.sleep(0.005)  # Simulate async operation
            return {
                "id": f"mock_tx_{id(self)}",
                "status": "active",
                "note": "Mock transaction - Rust engine not available"
            }
        
        async def commit_transaction(self, transaction_id: str) -> Dict[str, Any]:
            await asyncio.sleep(0.005)  # Simulate async operation
            return {
                "transaction_id": transaction_id,
                "status": "committed",
                "note": "Mock commit - Rust engine not available"
            }
        
        async def rollback_transaction(self, transaction_id: str) -> Dict[str, Any]:
            await asyncio.sleep(0.005)  # Simulate async operation
            return {
                "transaction_id": transaction_id,
                "status": "rolled_back",
                "note": "Mock rollback - Rust engine not available"
            }
        
        async def close(self) -> Dict[str, Any]:
            await asyncio.sleep(0.005)  # Simulate async operation
            return {
                "status": "closed",
                "note": "Mock close - Rust engine not available"
            }
    
    class MockOxenTransaction:
        """Mock implementation when Rust engine is not available."""
        
        def __init__(self, engine: MockOxenEngine, transaction_id: str):
            self.engine = engine
            self.transaction_id = transaction_id
        
        async def commit(self) -> Dict[str, Any]:
            return await self.engine.commit_transaction(self.transaction_id)
        
        async def rollback(self) -> Dict[str, Any]:
            return await self.engine.rollback_transaction(self.transaction_id)
        
        async def execute(self, sql: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
            return await self.engine.execute_query(sql, params)
    
    # Replace the classes with mock implementations
    OxenEngine = MockOxenEngine
    OxenTransaction = MockOxenTransaction 