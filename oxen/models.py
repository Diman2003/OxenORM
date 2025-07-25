#!/usr/bin/env python3
"""
OxenORM Model System

This module provides the core model functionality for OxenORM,
inspired by Tortoise ORM but optimized for OxenORM's architecture.
"""

import asyncio
import inspect
import re
from collections.abc import Awaitable, Callable, Generator, Iterable
from copy import copy, deepcopy
from functools import partial
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union, cast
from enum import Enum
from dataclasses import dataclass, field
import uuid
from datetime import datetime

from oxen.fields.base import Field
from oxen.fields.data import (
    IntegerField, CharField, TextField, BooleanField, DateTimeField,
    FloatField, DecimalField, JSONField, UUIDField
)
from oxen.fields.relational import (
    ForeignKeyField, ManyToManyField, OneToOneField
)
from oxen.exceptions import (
    ConfigurationError, DoesNotExist, FieldError, 
    IncompleteInstanceError, IntegrityError, OperationalError,
    ParamsError, ValidationError
)
from oxen.queryset import QuerySet, QuerySetSingle, Q
from oxen.manager import Manager
from oxen.signals import Signals
from oxen.validators import Validator

MODEL = TypeVar("MODEL", bound="Model")
EMPTY = object()


class OnDelete(str, Enum):
    """On delete behavior for foreign keys."""
    CASCADE = "CASCADE"
    RESTRICT = "RESTRICT"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    NO_ACTION = "NO ACTION"


@dataclass
class MetaInfo:
    """Meta information for a model."""
    table_name: str
    fields: Set[str] = field(default_factory=set)
    fields_map: Dict[str, Field] = field(default_factory=dict)
    db_fields: List[str] = field(default_factory=list)
    pk_attr: str = "id"
    pk_field: Optional[Field] = None
    generated_db_fields: Set[str] = field(default_factory=set)
    fetch_fields: Set[str] = field(default_factory=set)
    fk_fields: Set[str] = field(default_factory=set)
    o2o_fields: Set[str] = field(default_factory=set)
    m2m_fields: Set[str] = field(default_factory=set)
    backward_fk_fields: Set[str] = field(default_factory=set)
    backward_o2o_fields: Set[str] = field(default_factory=set)
    fields_db_projection: Dict[str, str] = field(default_factory=dict)
    db_native_fields: List[tuple] = field(default_factory=list)
    db_default_fields: List[tuple] = field(default_factory=list)
    db_complex_fields: List[tuple] = field(default_factory=list)
    ordering: tuple = ()
    unique_together: tuple = ()
    indexes: List = field(default_factory=list)
    constraints: List = field(default_factory=list)
    abstract: bool = False
    manager: Optional[Manager] = None
    db: Optional[Any] = None  # Will be set to database connection

    @property
    def full_name(self) -> str:
        """Get the full name of the model."""
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    def add_field(self, name: str, field_obj: Field) -> None:
        """Add a field to the model."""
        self.fields.add(name)
        self.fields_map[name] = field_obj
        field_obj.model_field_name = name
        
        if field_obj.primary_key:
            self.pk_attr = name
            self.pk_field = field_obj
        
        if field_obj.generated:
            self.generated_db_fields.add(name)
        
        if field_obj.has_db_field:
            self.db_fields.append(name)
            self.fields_db_projection[name] = field_obj.source_field or name

    def finalise_model(self) -> None:
        """Finalize model setup."""
        # Ensure we have a primary key
        if not self.pk_field:
            # Create default ID field
            id_field = IntegerField(primary_key=True, auto_increment=True)
            self.add_field("id", id_field)
            self.pk_attr = "id"
            self.pk_field = id_field

    def finalise_fields(self) -> None:
        """Finalize field setup."""
        # Categorize fields for database operations
        for name, field_obj in self.fields_map.items():
            if field_obj.skip_to_python_if_native:
                self.db_native_fields.append((name, name, field_obj))
            elif field_obj.to_python_value == Field.to_python_value:
                self.db_default_fields.append((name, name, field_obj))
            else:
                self.db_complex_fields.append((name, name, field_obj))


class ModelMeta(type):
    """Metaclass for Model classes."""
    
    def __new__(cls, name: str, bases: tuple, attrs: dict) -> ModelMeta:
        """Create a new model class."""
        # Check if this is an abstract model
        meta_class = attrs.get('Meta', None)
        is_abstract = getattr(meta_class, 'abstract', False) if meta_class else False
        
        if is_abstract:
            return super().__new__(cls, name, bases, attrs)
        
        # Parse fields
        fields_map = {}
        fields_db_projection = {}
        filters = {}
        fk_fields = set()
        o2o_fields = set()
        m2m_fields = set()
        
        # Extract fields from attributes
        for key, value in attrs.items():
            if isinstance(value, Field):
                fields_map[key] = value
                fields_db_projection[key] = value.source_field or key
                
                # Categorize relational fields
                if isinstance(value, ForeignKeyField):
                    fk_fields.add(key)
                elif isinstance(value, OneToOneField):
                    o2o_fields.add(key)
                elif isinstance(value, ManyToManyField):
                    m2m_fields.add(key)
        
        # Build meta info
        meta_info = MetaInfo(
            table_name=attrs.get('__tablename__', name.lower()),
            fields_map=fields_map,
            fields_db_projection=fields_db_projection,
            fk_fields=fk_fields,
            o2o_fields=o2o_fields,
            m2m_fields=m2m_fields,
            fields=set(fields_map.keys()),
            db_fields=list(fields_map.keys()),
            manager=Manager()
        )
        
        # Set up meta info
        meta_info.finalise_model()
        meta_info.finalise_fields()
        
        # Add meta info to class
        attrs['_meta'] = meta_info
        
        # Add manager
        if 'objects' not in attrs:
            attrs['objects'] = meta_info.manager
        
        return super().__new__(cls, name, bases, attrs)


class Model(metaclass=ModelMeta):
    """
    Base class for all OxenORM Models.
    
    This class provides the core functionality for model instances,
    including field management, database operations, and query building.
    """

    _meta: MetaInfo
    _listeners: Dict[Signals, Dict[Type['Model'], List[Callable]]] = {
        Signals.pre_save: {},
        Signals.post_save: {},
        Signals.pre_delete: {},
        Signals.post_delete: {},
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a model instance."""
        meta = self._meta
        self._partial = False
        self._saved_in_db = False
        self._custom_generated_pk = False
        self._await_when_save: Dict[str, Callable[[], Awaitable[Any]]] = {}

        # Assign defaults for missing fields
        for key in meta.fields.difference(self._set_kwargs(kwargs)):
            field_object = meta.fields_map[key]
            field_default = field_object.default
            if inspect.iscoroutinefunction(field_default):
                self._await_when_save[key] = field_default
            elif callable(field_default):
                setattr(self, key, field_default())
            else:
                setattr(self, key, deepcopy(field_object.default))

    def __setattr__(self, key: str, value: Any) -> None:
        """Set an attribute with validation."""
        # Clear async default function if field is set
        if hasattr(self, "_await_when_save"):
            self._await_when_save.pop(key, None)
        
        # Validate relational fields
        if key in self._meta.fk_fields or key in self._meta.o2o_fields:
            self._validate_relation_type(key, value)
        
        super().__setattr__(key, value)

    def _set_kwargs(self, kwargs: dict) -> Set[str]:
        """Set keyword arguments with validation."""
        meta = self._meta
        passed_fields = {*kwargs.keys()} | meta.fetch_fields

        for key, value in kwargs.items():
            if key in meta.fk_fields or key in meta.o2o_fields:
                if value and not value._saved_in_db:
                    raise OperationalError(
                        f"You should first call .save() on {value} before referring to it"
                    )
                setattr(self, key, value)
                passed_fields.add(meta.fields_map[key].source_field)
            elif key in meta.fields_db_projection:
                field_object = meta.fields_map[key]
                if field_object.primary_key and field_object.generated:
                    self._custom_generated_pk = True
                if value is None and not field_object.null:
                    raise ValueError(f"{key} is non nullable field, but null was passed")
                setattr(self, key, field_object.to_python_value(value))
            elif key in meta.backward_fk_fields:
                raise ConfigurationError(
                    "You can't set backward relations through init, change related model instead"
                )
            elif key in meta.backward_o2o_fields:
                raise ConfigurationError(
                    "You can't set backward one to one relations through init,"
                    " change related model instead"
                )
            elif key in meta.m2m_fields:
                raise ConfigurationError(
                    "You can't set m2m relations through init, use m2m_manager instead"
                )

        return passed_fields

    @classmethod
    def _init_from_db(cls: Type[MODEL], **kwargs: Any) -> MODEL:
        """Initialize a model instance from database data."""
        self = cls.__new__(cls)
        self._partial = False
        self._saved_in_db = True
        self._custom_generated_pk = self._meta.pk_attr not in self._meta.generated_db_fields
        self._await_when_save = {}

        meta = self._meta
        inited_keys: Set[str] = set()
        
        try:
            # Handle native fields (already converted by DB driver)
            for key, model_field, field in meta.db_native_fields:
                setattr(self, model_field, kwargs[key])
                inited_keys.add(key)
            
            # Handle default fields (simple type conversion)
            for key, model_field, field in meta.db_default_fields:
                if (value := kwargs[key]) is not None:
                    value = field.field_type(value)
                setattr(self, model_field, value)
                inited_keys.add(key)
            
            # Handle complex fields (need manual conversion)
            for key, model_field, field in meta.db_complex_fields:
                setattr(self, model_field, field.to_python_value(kwargs[key]))
                inited_keys.add(key)
        except KeyError:
            self._partial = True
            # Handle missing fields gracefully
            for key, value in kwargs.items():
                if key in inited_keys or key not in meta.fields_map:
                    continue
                field = meta.fields_map[key]
                setattr(self, key, field.to_python_value(value))

        return self

    def __str__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}>"

    def __repr__(self) -> str:
        """Detailed string representation."""
        if self.pk:
            return f"<{self.__class__.__name__}: {self.pk}>"
        return f"<{self.__class__.__name__}>"

    def __hash__(self) -> int:
        """Hash based on primary key."""
        if not self.pk:
            raise TypeError("Model instances without id are unhashable")
        return hash(self.pk)

    def __iter__(self) -> Iterable[tuple]:
        """Iterate over field-value pairs."""
        for field in self._meta.db_fields:
            yield field, getattr(self, field)

    def __eq__(self, other: object) -> bool:
        """Equality based on type and primary key."""
        return type(other) is type(self) and self.pk == other.pk

    def _get_pk_val(self) -> Any:
        """Get primary key value."""
        return getattr(self, self._meta.pk_attr, None)

    def _set_pk_val(self, value: Any) -> None:
        """Set primary key value."""
        setattr(self, self._meta.pk_attr, value)

    pk = property(_get_pk_val, _set_pk_val)

    @classmethod
    def _validate_relation_type(cls, field_key: str, value: Optional['Model']) -> None:
        """Validate relational field types."""
        if value is not None:
            field_object = cls._meta.fields_map[field_key]
            if not isinstance(value, field_object.related_model):
                raise ValidationError(
                    f"Field {field_key} expects {field_object.related_model.__name__}, "
                    f"got {type(value).__name__}"
                )

    @classmethod
    async def _getbypk(cls: Type[MODEL], key: Any) -> MODEL:
        """Get a model instance by primary key."""
        return await cls.get(pk=key)

    def clone(self: MODEL, pk: Any = EMPTY) -> MODEL:
        """Clone the model instance."""
        new_instance = self.__class__.__new__(self.__class__)
        new_instance._partial = self._partial
        new_instance._saved_in_db = False
        new_instance._custom_generated_pk = False
        new_instance._await_when_save = {}

        # Copy field values
        for field in self._meta.fields:
            value = getattr(self, field)
            if pk is not EMPTY and field == self._meta.pk_attr:
                setattr(new_instance, field, pk)
            else:
                setattr(new_instance, field, deepcopy(value))

        return new_instance

    def update_from_dict(self: MODEL, data: dict) -> MODEL:
        """Update model from dictionary."""
        for key, value in data.items():
            if key in self._meta.fields:
                setattr(self, key, value)
        return self

    @classmethod
    def register_listener(cls, signal: Signals, listener: Callable) -> None:
        """Register a signal listener."""
        if signal not in cls._listeners:
            cls._listeners[signal] = {}
        if cls not in cls._listeners[signal]:
            cls._listeners[signal][cls] = []
        cls._listeners[signal][cls].append(listener)

    async def _set_async_default_field(self) -> None:
        """Set async default fields."""
        for key, default_func in self._await_when_save.items():
            setattr(self, key, await default_func())

    async def _wait_for_listeners(self, signal: Signals, *listener_args) -> None:
        """Wait for signal listeners to complete."""
        if signal in self._listeners and self.__class__ in self._listeners[signal]:
            for listener in self._listeners[signal][self.__class__]:
                await listener(self, *listener_args)

    async def _pre_delete(self, using_db: Optional[Any] = None) -> None:
        """Pre-delete hook."""
        await self._wait_for_listeners(Signals.pre_delete, using_db)

    async def _post_delete(self, using_db: Optional[Any] = None) -> None:
        """Post-delete hook."""
        await self._wait_for_listeners(Signals.post_delete, using_db)

    async def _pre_save(
        self,
        using_db: Optional[Any] = None,
        update_fields: Optional[Iterable[str]] = None,
    ) -> None:
        """Pre-save hook."""
        await self._wait_for_listeners(Signals.pre_save, using_db, update_fields)

    async def _post_save(
        self,
        using_db: Optional[Any] = None,
        created: bool = False,
        update_fields: Optional[Iterable[str]] = None,
    ) -> None:
        """Post-save hook."""
        await self._wait_for_listeners(Signals.post_save, using_db, created, update_fields)

    async def save(
        self,
        using_db: Optional[Any] = None,
        update_fields: Optional[Iterable[str]] = None,
        force_create: bool = False,
        force_update: bool = False,
    ) -> None:
        """Save the model instance to the database."""
        # Set async default fields
        await self._set_async_default_field()

        # Pre-save hook
        await self._pre_save(using_db, update_fields)

        # Determine if this is a create or update
        if force_create or (not self._saved_in_db and not force_update):
            # Create new record
            created = True
            # Generate primary key if needed
            if self._meta.pk_field and self._meta.pk_field.generated and not self.pk:
                if isinstance(self._meta.pk_field, IntegerField):
                    # For now, use a simple increment - in real implementation,
                    # this would come from the database
                    self.pk = int(uuid.uuid4().hex[:8], 16)
                elif isinstance(self._meta.pk_field, UUIDField):
                    self.pk = uuid.uuid4()
            
            # Insert into database
            # This would be implemented with actual database operations
            self._saved_in_db = True
        else:
            # Update existing record
            created = False
            if not self.pk:
                raise IntegrityError("Cannot update model without primary key")
            
            # Update in database
            # This would be implemented with actual database operations
            pass

        # Post-save hook
        await self._post_save(using_db, created, update_fields)

    async def delete(self, using_db: Optional[Any] = None) -> None:
        """Delete the model instance from the database."""
        if not self.pk:
            raise IntegrityError("Cannot delete model without primary key")

        # Pre-delete hook
        await self._pre_delete(using_db)

        # Delete from database
        # This would be implemented with actual database operations
        self._saved_in_db = False

        # Post-delete hook
        await self._post_delete(using_db)

    @classmethod
    def _choose_db(cls, for_write: bool = False) -> Any:
        """Choose database connection."""
        # This would be implemented with actual database connection management
        return cls._meta.db

    @classmethod
    async def get_or_create(
        cls,
        defaults: Optional[dict] = None,
        using_db: Optional[Any] = None,
        **kwargs: Any,
    ) -> tuple['Model', bool]:
        """Get an existing object or create a new one."""
        defaults = defaults or {}
        try:
            return await cls.get(**kwargs), False
        except DoesNotExist:
            obj = cls(**kwargs)
            for key, value in defaults.items():
                setattr(obj, key, value)
            await obj.save(using_db=using_db)
            return obj, True

    @classmethod
    def _db_queryset(
        cls, using_db: Optional[Any] = None, for_write: bool = False
    ) -> QuerySet['Model']:
        """Get a queryset for database operations."""
        db = using_db or cls._choose_db(for_write)
        return QuerySet(cls, db)

    @classmethod
    async def create(
        cls: Type[MODEL], using_db: Optional[Any] = None, **kwargs: Any
    ) -> MODEL:
        """Create a new model instance and save it."""
        obj = cls(**kwargs)
        await obj.save(using_db=using_db)
        return obj

    @classmethod
    def filter(cls, *args: Q, **kwargs: Any) -> QuerySet['Model']:
        """Filter queryset."""
        return cls._db_queryset().filter(*args, **kwargs)

    @classmethod
    def exclude(cls, *args: Q, **kwargs: Any) -> QuerySet['Model']:
        """Exclude from queryset."""
        return cls._db_queryset().exclude(*args, **kwargs)

    @classmethod
    def all(cls, using_db: Optional[Any] = None) -> QuerySet['Model']:
        """Get all instances."""
        return cls._db_queryset(using_db)

    @classmethod
    def get(
        cls, *args: Q, using_db: Optional[Any] = None, **kwargs: Any
    ) -> QuerySetSingle['Model']:
        """Get a single instance."""
        return cls._db_queryset(using_db).get(*args, **kwargs)

    @classmethod
    def first(cls, using_db: Optional[Any] = None) -> QuerySetSingle[Optional['Model']]:
        """Get the first instance."""
        return cls._db_queryset(using_db).first()

    @classmethod
    def last(cls, using_db: Optional[Any] = None) -> QuerySetSingle[Optional['Model']]:
        """Get the last instance."""
        return cls._db_queryset(using_db).last()

    @classmethod
    def exists(
        cls, *args: Q, using_db: Optional[Any] = None, **kwargs: Any
    ) -> QuerySet:
        """Check if any instances exist."""
        return cls._db_queryset(using_db).exists(*args, **kwargs)

    @classmethod
    def count(
        cls, *args: Q, using_db: Optional[Any] = None, **kwargs: Any
    ) -> QuerySet:
        """Count instances."""
        return cls._db_queryset(using_db).count(*args, **kwargs)

    @classmethod
    def get_or_none(
        cls, *args: Q, using_db: Optional[Any] = None, **kwargs: Any
    ) -> QuerySetSingle[Optional['Model']]:
        """Get a single instance or None."""
        return cls._db_queryset(using_db).get_or_none(*args, **kwargs)

    def __await__(self: MODEL) -> Generator[Any, None, MODEL]:
        """Make model instances awaitable."""
        async def _self() -> MODEL:
            return self
        return _self().__await__()

    class Meta:
        """Meta class for model configuration."""
        abstract = False
        table_name: Optional[str] = None
        ordering: tuple = ()
        unique_together: tuple = ()
        indexes: List = None
        constraints: List = None 