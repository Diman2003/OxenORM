"""
OxenORM Model System
Provides a Django-like model system with field types and validation
"""

import asyncio
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, TYPE_CHECKING
from datetime import datetime, date, time
from decimal import Decimal
import uuid
from dataclasses import dataclass, field
from enum import Enum

from .fields import (
    Field, CharField, TextField, IntegerField, FloatField, DecimalField,
    BooleanField, DateTimeField, DateField, TimeField, UUIDField
)
from .exceptions import ValidationError, ModelError

if TYPE_CHECKING:
    from .queryset import QuerySet

T = TypeVar('T', bound='Model')

class ModelMeta:
    """Meta class for model configuration"""
    def __init__(self, **kwargs):
        self.db_table = kwargs.get('db_table')
        self.ordering = kwargs.get('ordering', [])
        self.indexes = kwargs.get('indexes', [])
        self.unique_together = kwargs.get('unique_together', [])
        self.abstract = kwargs.get('abstract', False)

class Model:
    """
    Base model class for OxenORM
    Provides Django-like model functionality with async support
    """
    
    # Meta configuration
    Meta: Optional[ModelMeta] = None
    
    # Internal fields
    _fields: Dict[str, Field] = {}
    _pk_field: Optional[str] = None
    _table_name: Optional[str] = None
    _is_initialized: bool = False
    
    def __init__(self, **kwargs):
        """Initialize model instance with field values"""
        self._data = {}
        self._changed_fields = set()
        self._is_new = True
        self._pk_value = None
        
        # Set field values from kwargs
        for field_name, value in kwargs.items():
            if field_name in self._fields:
                setattr(self, field_name, value)
            else:
                raise ModelError(f"Unknown field '{field_name}' for model {self.__class__.__name__}")
    
    def __class_getitem__(cls, item):
        """Support for generic type hints"""
        return cls
    
    @classmethod
    def _initialize_model(cls):
        """Initialize model fields and metadata"""
        if cls._is_initialized:
            return
        
        # Collect fields from class attributes
        fields = {}
        pk_field = None
        
        for attr_name, attr_value in cls.__dict__.items():
            if isinstance(attr_value, Field):
                fields[attr_name] = attr_value
                attr_value.name = attr_name
                attr_value.model = cls
                
                if attr_value.primary_key:
                    if pk_field:
                        raise ModelError(f"Multiple primary key fields defined: {pk_field} and {attr_name}")
                    pk_field = attr_name
        
        # Set default primary key if none specified
        if not pk_field:
            pk_field = 'id'
            if 'id' not in fields:
                fields['id'] = IntegerField(primary_key=True, auto_increment=True)
                fields['id'].name = 'id'
                fields['id'].model = cls
        
        cls._fields = fields
        cls._pk_field = pk_field
        
        # Set table name
        if cls.Meta and cls.Meta.db_table:
            cls._table_name = cls.Meta.db_table
        else:
            cls._table_name = cls._get_default_table_name()
        
        cls._is_initialized = True
    
    @classmethod
    def _get_default_table_name(cls) -> str:
        """Generate default table name from class name"""
        name = cls.__name__
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(?!^)([A-Z][a-z]+)', r'_\1', name).lower()
        return f"{name}s"
    
    @classmethod
    def objects(cls) -> 'QuerySet':
        """Get QuerySet for this model"""
        cls._initialize_model()
        from .queryset import QuerySet
        return QuerySet(cls)
    
    @classmethod
    async def create(cls, **kwargs) -> T:
        """Create and save a new model instance"""
        instance = cls(**kwargs)
        await instance.save()
        return instance
    
    @classmethod
    async def get(cls, **kwargs) -> T:
        """Get a single model instance"""
        return await cls.objects().get(**kwargs)
    
    @classmethod
    async def get_or_create(cls, defaults: Optional[Dict] = None, **kwargs) -> tuple[T, bool]:
        """Get an existing instance or create a new one"""
        defaults = defaults or {}
        try:
            instance = await cls.get(**kwargs)
            return instance, False
        except cls.DoesNotExist:
            # Combine kwargs and defaults
            create_kwargs = {**kwargs, **defaults}
            instance = await cls.create(**create_kwargs)
            return instance, True
    
    @classmethod
    async def update_or_create(cls, defaults: Optional[Dict] = None, **kwargs) -> tuple[T, bool]:
        """Update an existing instance or create a new one"""
        defaults = defaults or {}
        try:
            instance = await cls.get(**kwargs)
            for field, value in defaults.items():
                setattr(instance, field, value)
            await instance.save()
            return instance, False
        except cls.DoesNotExist:
            create_kwargs = {**kwargs, **defaults}
            instance = await cls.create(**create_kwargs)
            return instance, True
    
    @classmethod
    async def bulk_create(cls, instances: List[T], batch_size: int = 100) -> List[T]:
        """Create multiple instances efficiently"""
        if not instances:
            return []
        
        # Group instances into batches
        batches = [instances[i:i + batch_size] for i in range(0, len(instances), batch_size)]
        created_instances = []
        
        for batch in batches:
            # Convert instances to data dictionaries
            batch_data = []
            for instance in batch:
                data = {}
                for field_name, field in cls._fields.items():
                    if field_name in instance._data:
                        data[field_name] = instance._data[field_name]
                batch_data.append(data)
            
            # Perform bulk insert
            # TODO: Implement actual bulk insert when engine is ready
            for instance in batch:
                instance._is_new = False
                created_instances.append(instance)
        
        return created_instances
    
    def __getattr__(self, name: str) -> Any:
        """Get field value"""
        if name in self._fields:
            return self._data.get(name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any):
        """Set field value with validation"""
        if name.startswith('_'):
            super().__setattr__(name, value)
            return
        
        if name in self._fields:
            field = self._fields[name]
            # Validate value
            validated_value = field.validate(value)
            self._data[name] = validated_value
            self._changed_fields.add(name)
            
            # Set primary key value
            if field.primary_key:
                self._pk_value = validated_value
        else:
            super().__setattr__(name, value)
    
    async def save(self, force_insert: bool = False, force_update: bool = False):
        """Save the model instance to the database"""
        self.__class__._initialize_model()
        
        # Validate all fields
        self.full_clean()
        
        # Prepare data for save
        data = {}
        for field_name, field in self._fields.items():
            if field_name in self._data:
                data[field_name] = field.to_db_value(self._data[field_name])
        
        # Determine if this is an insert or update
        if force_insert or (self._is_new and not force_update):
            # Insert
            # TODO: Implement actual insert when engine is ready
            if self._pk_field in data:
                self._pk_value = data[self._pk_field]
            self._is_new = False
        else:
            # Update
            if not self._pk_value:
                raise ModelError("Cannot update instance without primary key")
            # TODO: Implement actual update when engine is ready
        
        self._changed_fields.clear()
    
    async def delete(self):
        """Delete the model instance from the database"""
        if self._is_new:
            return
        
        if not self._pk_value:
            raise ModelError("Cannot delete instance without primary key")
        
        # TODO: Implement actual delete when engine is ready
        self._is_new = True
        self._pk_value = None
    
    def refresh_from_db(self):
        """Refresh instance data from database"""
        if self._is_new:
            raise ModelError("Cannot refresh new instance")
        
        # TODO: Implement actual refresh when engine is ready
        pass
    
    def full_clean(self):
        """Validate all fields"""
        errors = {}
        
        for field_name, field in self._fields.items():
            if field_name in self._data:
                try:
                    field.validate(self._data[field_name])
                except ValidationError as e:
                    errors[field_name] = e
        
        if errors:
            raise ValidationError(errors)
    
    def clean(self):
        """Custom validation method to be overridden by subclasses"""
        pass
    
    @property
    def pk(self) -> Any:
        """Get primary key value"""
        return self._pk_value
    
    @property
    def is_new(self) -> bool:
        """Check if instance is new (not saved)"""
        return self._is_new
    
    def __repr__(self) -> str:
        """String representation of the model instance"""
        attrs = []
        for field_name in self._fields.keys():
            if field_name in self._data:
                attrs.append(f"{field_name}={repr(self._data[field_name])}")
        
        return f"{self.__class__.__name__}({', '.join(attrs)})"
    
    def __str__(self) -> str:
        """String representation for display"""
        return self.__repr__()
    
    # Exception classes
    class DoesNotExist(Exception):
        """Raised when a model instance is not found"""
        pass
    
    class MultipleObjectsReturned(Exception):
        """Raised when multiple model instances are returned when expecting one"""
        pass

# Convenience function for creating models
def create_model(name: str, fields: Dict[str, Field], **meta_options) -> Type[Model]:
    """Create a model class dynamically"""
    meta = ModelMeta(**meta_options)
    
    # Create class attributes
    attrs = {
        '__module__': '__main__',
        'Meta': meta,
    }
    
    # Add fields
    for field_name, field in fields.items():
        attrs[field_name] = field
    
    # Create the class
    model_class = type(name, (Model,), attrs)
    
    # Initialize the model
    model_class._initialize_model()
    
    return model_class 