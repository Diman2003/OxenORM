"""
OxenORM - High-performance Python ORM with Rust backend
"""

__version__ = "0.1.0"
__author__ = "OxenORM Team"

# Core imports
from .models import Model, ModelMeta
from .fields import Field
from .exceptions import ValidationError, ModelError, DoesNotExist, MultipleObjectsReturned

# Try to import Rust backend (optional)
try:
    from .rust_bridge import OxenEngine
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    OxenEngine = None

__all__ = [
    'Model', 'ModelMeta', 'Field', 'ValidationError', 'ModelError', 
    'DoesNotExist', 'MultipleObjectsReturned', 'OxenEngine', 'RUST_AVAILABLE'
] 