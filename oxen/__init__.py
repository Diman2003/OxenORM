"""
OxenORM - High-performance Python ORM with Rust backend
"""

__version__ = "0.1.0"
__author__ = "OxenORM Team"

# Core imports
from .models import Model, ModelMeta
from .fields import Field
from .exceptions import (
    ValidationError, ModelError, DoesNotExist, MultipleObjectsReturned,
    IncompleteInstanceError, IntegrityError, OperationalError, ParamsError
)
from .queryset import QuerySet, AwaitableQuery, QuerySetSingle
from .manager import Manager
from .signals import Signals
from .validators import Validator

# Try to import Rust backend (optional)
try:
    from .rust_bridge import OxenEngine
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    OxenEngine = None

__all__ = [
    'Model', 'ModelMeta', 'Field', 'ValidationError', 'ModelError', 
    'DoesNotExist', 'MultipleObjectsReturned', 'IncompleteInstanceError',
    'IntegrityError', 'OperationalError', 'ParamsError', 'QuerySet',
    'AwaitableQuery', 'QuerySetSingle', 'Manager', 'Signals', 'Validator',
    'OxenEngine', 'RUST_AVAILABLE'
] 