"""
Database connection management for OxenORM

This module handles database initialization and connection management,
integrating with the Rust backend for high-performance operations.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Type
from .rust_bridge import OxenEngine
from .models import Model
from .exceptions import OxenError


class DatabaseManager:
    """Manages database connections and model registration."""
    
    _instance: Optional[DatabaseManager] = None
    _lock = asyncio.Lock()
    _engine: Optional[OxenEngine] = None
    _models: List[Type[Model]] = []
    _initialized = False
    
    def __new__(cls) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def initialize(
        cls,
        databases: Dict[str, str],
        models: Optional[List[Type[Model]]] = None
    ) -> None:
        """Initialize the database manager with connection strings and models."""
        async with cls._lock:
            if cls._initialized:
                return
            
            # Get the default database connection
            if 'default' not in databases:
                raise OxenError("Default database connection required")
            
            default_connection = databases['default']
            
            # Initialize Rust engine
            cls._engine = OxenEngine(default_connection)
            await cls._engine.connect()
            
            # Register models
            if models:
                cls._models = models
                for model_class in models:
                    model_class._set_rust_engine(cls._engine)
            
            cls._initialized = True
    
    @classmethod
    async def close(cls) -> None:
        """Close all database connections."""
        async with cls._lock:
            if cls._engine:
                await cls._engine.disconnect()
                cls._engine = None
            
            cls._models.clear()
            cls._initialized = False
    
    @classmethod
    def get_engine(cls) -> Optional[OxenEngine]:
        """Get the Rust engine instance."""
        return cls._engine
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the database manager is initialized."""
        return cls._initialized


async def init_db(
    databases: Dict[str, str],
    models: Optional[List[Type[Model]]] = None
) -> None:
    """
    Initialize the database connections.
    
    Args:
        databases: Dictionary mapping database names to connection strings
        models: List of model classes to register
    """
    await DatabaseManager.initialize(databases, models)


async def close_db() -> None:
    """Close all database connections."""
    await DatabaseManager.close()


def get_engine() -> Optional[OxenEngine]:
    """Get the Rust engine instance."""
    return DatabaseManager.get_engine()


def is_initialized() -> bool:
    """Check if the database is initialized."""
    return DatabaseManager.is_initialized() 