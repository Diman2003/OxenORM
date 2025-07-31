"""
OxenORM - High-performance Python ORM with Rust backend
"""

__version__ = "0.1.0"
__author__ = "OxenORM Team"

# Configure uvloop for enhanced performance
from .uvloop_config import configure_uvloop, is_uvloop_active, get_event_loop_info

# Core imports
from .models import Model, ModelMeta, set_database_for_models
from .fields import (
    Field, CharField, TextField, IntField, IntegerField, FloatField, DecimalField,
    BooleanField, DateField, DateTimeField, TimeField, UUIDField, JSONField,
    BinaryField, EmailField, URLField, SlugField, FileField, ImageField,
    ForeignKeyField, OneToOneField, ManyToManyField,
    ArrayField, RangeField, HStoreField, JSONBField, GeometryField
)
from .exceptions import (
    ValidationError, ModelError, DoesNotExist, MultipleObjectsReturned,
    IncompleteInstanceError, IntegrityError, OperationalError, ParamsError
)
from .queryset import QuerySet, AwaitableQuery, QuerySetSingle
from .manager import Manager
from .signals import Signals
from .validators import Validator
from .engine import connect, disconnect
from .file_operations import FileOperations, FileManager, ImageProcessor

# Try to import Rust backend (optional)
try:
    from .rust_bridge import OxenEngine
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    OxenEngine = None

__all__ = [
    'Model', 'ModelMeta', 'set_database_for_models',
    'Field', 'CharField', 'TextField', 'IntField', 'IntegerField', 'FloatField', 'DecimalField',
    'BooleanField', 'DateField', 'DateTimeField', 'TimeField', 'UUIDField', 'JSONField',
    'BinaryField', 'EmailField', 'URLField', 'SlugField', 'FileField', 'ImageField',
    'ForeignKeyField', 'OneToOneField', 'ManyToManyField',
    'ArrayField', 'RangeField', 'HStoreField', 'JSONBField', 'GeometryField',
    'ValidationError', 'ModelError', 'DoesNotExist', 'MultipleObjectsReturned',
    'IncompleteInstanceError', 'IntegrityError', 'OperationalError', 'ParamsError',
    'QuerySet', 'AwaitableQuery', 'QuerySetSingle', 'Manager', 'Signals', 'Validator',
    'connect', 'disconnect', 'FileOperations', 'FileManager', 'ImageProcessor',
    'OxenEngine', 'RUST_AVAILABLE',
    'configure_uvloop', 'is_uvloop_active', 'get_event_loop_info'
] 