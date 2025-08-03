"""
Relational field types for OxenORM

This module provides field types for defining relationships between models.
"""

from __future__ import annotations

from typing import Any, Optional, Type, TypeVar, Union, List, Dict
from .base import Field

T = TypeVar('T')


class LazyRelatedObject:
    """Lazy loading wrapper for related objects."""
    
    def __init__(self, model_class: Type[Any], pk_value: Any, field_name: str):
        self.model_class = model_class
        self.pk_value = pk_value
        self.field_name = field_name
        self._cached_value = None
        self._loaded = False
    
    async def _load(self) -> Any:
        """Load the related object from the database."""
        if not self._loaded:
            try:
                self._cached_value = await self.model_class.get(pk=self.pk_value)
                self._loaded = True
            except Exception:
                self._cached_value = None
                self._loaded = True
        return self._cached_value
    
    @property
    def pk(self) -> Any:
        """Get the primary key value directly."""
        return self.pk_value
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the loaded object."""
        if name in ['_load', '_cached_value', '_loaded', 'model_class', 'pk_value', 'field_name', 'pk']:
            return super().__getattr__(name)
        
        # Trigger loading if not already loaded
        if not self._loaded:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, we can't load synchronously
                    raise RuntimeError(f"Cannot access {name} on lazy-loaded object. Use await obj.{self.field_name} to load it first.")
                else:
                    # We can run the async load
                    self._cached_value = loop.run_until_complete(self._load())
                    self._loaded = True
            except RuntimeError:
                raise RuntimeError(f"Cannot access {name} on lazy-loaded object. Use await obj.{self.field_name} to load it first.")
        
        if self._cached_value is None:
            raise AttributeError(f"Related object not found for {self.field_name}")
        
        return getattr(self._cached_value, name)
    
    def __str__(self) -> str:
        if self._loaded and self._cached_value:
            return str(self._cached_value)
        return f"<LazyRelatedObject: {self.model_class.__name__}(pk={self.pk_value})>"
    
    def __repr__(self) -> str:
        return self.__str__()


class ReverseAccessor:
    """Reverse accessor for related objects."""
    
    def __init__(self, model_class: Type[Any], related_field: str, related_model: Type[Any]):
        self.model_class = model_class
        self.related_field = related_field
        self.related_model = related_model
    
    def __get__(self, instance: Any, owner: Type[Any]) -> Any:
        """Get the reverse accessor."""
        if instance is None:
            return self
        
        # Return a QuerySet for the related objects
        # The related_field is the field name in the related model that references this model
        from oxen.queryset import QuerySet
        from oxen.fields.relational import OneToOneField
        
        # Check if this is a one-to-one relationship
        # For one-to-one, we should return a single object, not a QuerySet
        if hasattr(self.related_model, '_meta'):
            field_obj = self.related_model._meta.fields_map.get(self.related_field)
            if field_obj and isinstance(field_obj, OneToOneField):
                # For one-to-one, return the first (and only) object
                queryset = QuerySet(self.related_model).filter(**{self.related_field: instance.pk})
                return queryset.first()
        
        # For foreign key and many-to-many, return QuerySet
        return QuerySet(self.related_model).filter(**{self.related_field: instance.pk})
    
    def __str__(self) -> str:
        return f"<ReverseAccessor: {self.related_model.__name__}.{self.related_field}>"


class RelationalField(Field):
    """Base class for all relational fields."""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.is_relational = True
        self.lazy_loading = kwargs.get('lazy_loading', True)
    
    def _validate(self, value: Any) -> Any:
        """Base validation for relational fields."""
        return self._validate_value(value)
    
    def _validate_value(self, value: Any) -> Any:
        """Base validation for relational fields."""
        return value
    
    def to_db_value(self, value: Any) -> Any:
        """Convert Python value to database value."""
        if value is None:
            return None
        if hasattr(value, 'pk'):
            return value.pk
        # Handle lazy objects that have pk_value
        if hasattr(value, 'pk_value'):
            return value.pk_value
        return value
    
    def from_db_value(self, value: Any) -> Any:
        """Convert database value to Python value."""
        if value is None:
            return None
        
        if self.lazy_loading:
            # Return a lazy loading wrapper
            return LazyRelatedObject(self._get_related_model(), value, self.model_field_name)
        else:
            # For now, just return the value as-is
            # In a full implementation, this would fetch the related model instance
            return value
    
    def _get_related_model(self) -> Type[Any]:
        """Get the related model class."""
        if isinstance(self.model, str):
            # Resolve the model class from string
            from oxen.models import get_model_registry
            registry = get_model_registry()
            return registry.get(self.model)
        else:
            return self.model
    
    def _get_sql_type(self) -> str:
        """Get the SQL type for this field."""
        raise NotImplementedError("Subclasses must implement _get_sql_type")


class ForeignKeyField(RelationalField):
    """Foreign key field for referencing other models."""
    
    def __init__(
        self,
        model: Union[str, Type[Any]],
        related_name: Optional[str] = None,
        on_delete: str = "CASCADE",
        on_update: str = "CASCADE",
        primary_key: bool = False,
        unique: bool = False,
        null: bool = True,
        default: Optional[Any] = None,
        lazy_loading: bool = True,
        **kwargs: Any
    ) -> None:
        super().__init__(
            primary_key=primary_key,
            unique=unique,
            null=null,
            default=default,
            lazy_loading=lazy_loading,
            **kwargs
        )
        self.model = model
        self.related_name = related_name
        self.on_delete = on_delete
        self.on_update = on_update
    
    def _validate_value(self, value: Any) -> Any:
        """Validate that the value is a valid foreign key."""
        if value is None:
            return None
        
        # For now, just ensure it's a valid ID
        if isinstance(value, (int, str)):
            return value
        elif hasattr(value, 'pk'):
            return value.pk
        else:
            raise ValueError("Value must be an ID or model instance")
    
    def from_db_value(self, value: Any) -> Any:
        """Convert database value to Python value."""
        if value is None:
            return None
        
        if self.lazy_loading:
            # Return a lazy loading wrapper
            return LazyRelatedObject(self._get_related_model(), value, self.model_field_name)
        else:
            # For now, just return the value as-is
            # In a full implementation, this would fetch the related model instance
            return value
    
    def _get_sql_type(self) -> str:
        """Get the SQL type for this field."""
        # Assume integer foreign keys for now
        return "BIGINT"
    
    def setup_reverse_accessor(self, model_class: Type[Any], field_name: str) -> None:
        """Setup reverse accessor on the related model."""
        if self.related_name:
            # Create reverse accessor
            # The related_field should be the field name in the current model that references the related model
            # The related_model should be the current model (the one with the foreign key)
            reverse_accessor = ReverseAccessor(model_class, field_name, model_class)
            setattr(self._get_related_model(), self.related_name, reverse_accessor)


class OneToOneField(ForeignKeyField):
    """One-to-one field for referencing other models."""
    
    def __init__(
        self,
        model: Union[str, Type[Any]],
        related_name: Optional[str] = None,
        on_delete: str = "CASCADE",
        on_update: str = "CASCADE",
        primary_key: bool = False,
        null: bool = True,
        default: Optional[Any] = None,
        lazy_loading: bool = True,
        **kwargs: Any
    ) -> None:
        super().__init__(
            model=model,
            related_name=related_name,
            on_delete=on_delete,
            on_update=on_update,
            primary_key=primary_key,
            null=null,
            default=default,
            lazy_loading=lazy_loading,
            **kwargs
        )
        self.unique = True  # One-to-one fields are always unique


class ManyToManyField(RelationalField):
    """Many-to-many field for referencing other models."""
    
    def __init__(
        self,
        model: Union[str, Type[Any]],
        through: Optional[Union[str, Type[Any]]] = None,
        related_name: Optional[str] = None,
        lazy_loading: bool = True,
        **kwargs: Any
    ) -> None:
        super().__init__(lazy_loading=lazy_loading, **kwargs)
        self.model = model
        self.through = through
        self.related_name = related_name
    
    def _validate_value(self, value: Any) -> Any:
        """Validate that the value is a valid many-to-many relationship."""
        if value is None:
            return None
        
        # For many-to-many, we expect a list or QuerySet
        if isinstance(value, (list, tuple)):
            return value
        else:
            raise ValueError("Many-to-many field expects a list or QuerySet")
    
    def from_db_value(self, value: Any) -> Any:
        """Convert database value to Python value."""
        if value is None:
            return None
        
        if self.lazy_loading:
            # Return a lazy loading wrapper for many-to-many
            # This would need to be implemented differently for M2M
            return value
        else:
            return value
    
    def _get_sql_type(self) -> str:
        """Get the SQL type for this field."""
        # Many-to-many fields don't create columns in the main table
        return "TEXT" 