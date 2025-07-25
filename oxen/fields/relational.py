"""
Relational field types for OxenORM

This module provides field types for defining relationships between models.
"""

from __future__ import annotations

from typing import Any, Optional, Type, TypeVar, Union
from .base import Field

T = TypeVar('T')


class RelationalField(Field):
    """Base class for all relational fields."""
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.is_relational = True
    
    def _validate_value(self, value: Any) -> Any:
        """Base validation for relational fields."""
        return value
    
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
        **kwargs: Any
    ) -> None:
        super().__init__(
            primary_key=primary_key,
            unique=unique,
            null=null,
            default=default,
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
    
    def _get_sql_type(self) -> str:
        """Get the SQL type for this field."""
        # Assume integer foreign keys for now
        return "BIGINT"


class OneToOneField(ForeignKeyField):
    """One-to-one relationship field."""
    
    def __init__(
        self,
        model: Union[str, Type[Any]],
        related_name: Optional[str] = None,
        on_delete: str = "CASCADE",
        on_update: str = "CASCADE",
        primary_key: bool = False,
        null: bool = True,
        default: Optional[Any] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(
            model=model,
            related_name=related_name,
            on_delete=on_delete,
            on_update=on_update,
            primary_key=primary_key,
            unique=True,  # OneToOne fields are always unique
            null=null,
            default=default,
            **kwargs
        )


class ManyToManyField(RelationalField):
    """Many-to-many relationship field."""
    
    def __init__(
        self,
        model: Union[str, Type[Any]],
        through: Optional[Union[str, Type[Any]]] = None,
        related_name: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.model = model
        self.through = through
        self.related_name = related_name
    
    def _validate_value(self, value: Any) -> Any:
        """Validate that the value is a list of model instances or IDs."""
        if value is None:
            return []
        
        if isinstance(value, (list, tuple)):
            return value
        else:
            raise ValueError("Value must be a list of model instances or IDs")
    
    def _get_sql_type(self) -> str:
        """Many-to-many fields don't have a direct SQL type."""
        raise NotImplementedError("ManyToManyField does not have a direct SQL type") 