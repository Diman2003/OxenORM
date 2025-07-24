"""
Tortoise ORM Integration for OxenORM Rust Backend

This module registers our Rust backend with Tortoise ORM so it can be used
with the 'rust://' URL scheme.
"""

import asyncio
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.backends.base.config_generator import expand_db_url
from tortoise.backends.base.executor import BaseExecutor
from tortoise.backends.base.schema_generator import BaseSchemaGenerator
from tortoise.connection import connections
from tortoise.exceptions import ConfigurationError, TransactionManagementError

from .rust_backend import RustBackendClient, RustBackendCapabilities


def register_rust_backend():
    """Register the Rust backend with Tortoise ORM."""
    
    # Monkey patch the expand_db_url function to handle our 'rust://' scheme
    original_expand_db_url = expand_db_url
    
    def patched_expand_db_url(db_url: str, testing: bool = False) -> Dict[str, Any]:
        """Patched version that handles the 'rust://' scheme."""
        parsed = urlparse(db_url)
        
        if parsed.scheme == "rust":
            # Extract connection details from the URL
            host = parsed.hostname or "localhost"
            port = parsed.port or 5432
            database = parsed.path.lstrip("/") or "oxenorm"
            username = parsed.username or "oxenorm"
            password = parsed.password or ""
            
            return {
                "engine": "oxen.rust_backend",
                "credentials": {
                    "host": host,
                    "port": port,
                    "database": database,
                    "user": username,
                    "password": password,
                },
                "connection_string": db_url,
            }
        else:
            # Fall back to original function for other schemes
            return original_expand_db_url(db_url, testing)
    
    # Replace the function
    import tortoise.backends.base.config_generator
    tortoise.backends.base.config_generator.expand_db_url = patched_expand_db_url
    
    print("✅ Rust backend registered with Tortoise ORM")


# Auto-register when module is imported
register_rust_backend()


class OxenTortoiseIntegration:
    """
    Integration class that provides a high-level interface for using
    Tortoise ORM with our Rust backend.
    """
    
    def __init__(self, db_url: str = "rust://localhost/oxenorm"):
        self.db_url = db_url
        self._initialized = False
    
    async def init(self, modules: Optional[Dict[str, List[str]]] = None):
        """Initialize Tortoise ORM with our Rust backend."""
        from tortoise import Tortoise
        
        # Initialize Tortoise with our backend
        await Tortoise.init(
            db_url=self.db_url,
            modules=modules or {"models": []},
            use_tz=False,
            _create_db=True,
        )
        
        self._initialized = True
        print(f"✅ Tortoise ORM initialized with Rust backend: {self.db_url}")
    
    async def generate_schemas(self):
        """Generate database schemas."""
        if not self._initialized:
            raise RuntimeError("Tortoise ORM not initialized. Call init() first.")
        
        from tortoise import Tortoise
        await Tortoise.generate_schemas()
        print("✅ Database schemas generated")
    
    async def close(self):
        """Close all database connections."""
        if not self._initialized:
            return
        
        from tortoise import Tortoise
        await Tortoise.close_connections()
        self._initialized = False
        print("✅ Database connections closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.init()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience function for quick setup
async def init_oxenorm(db_url: str = "rust://localhost/oxenorm", modules: Optional[Dict[str, List[str]]] = None):
    """
    Quick initialization function for OxenORM with Tortoise.
    
    Args:
        db_url: Database URL with 'rust://' scheme
        modules: Tortoise modules configuration
    
    Returns:
        OxenTortoiseIntegration instance
    """
    integration = OxenTortoiseIntegration(db_url)
    await integration.init(modules)
    return integration


# Example usage and testing
async def test_integration():
    """Test the integration between Tortoise ORM and our Rust backend."""
    
    print("🧪 Testing OxenORM + Tortoise Integration")
    print("=" * 50)
    
    try:
        # Test with our integration
        async with OxenTortoiseIntegration("rust://localhost/test_db") as oxen:
            await oxen.generate_schemas()
            print("✅ Integration test successful!")
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_integration()) 