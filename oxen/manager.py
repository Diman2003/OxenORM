#!/usr/bin/env python3
"""
OxenORM Manager System

This module provides the manager functionality for OxenORM,
which acts as the interface between models and querysets.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from oxen.models import Model
    from oxen.queryset import QuerySet

MODEL = TypeVar("MODEL", bound="Model")


class Manager:
    """
    Manager class that provides the interface between models and querysets.
    
    This class is responsible for creating and managing querysets for models.
    """

    def __init__(self, model: Optional[Type["Model"]] = None):
        """Initialize the manager."""
        self.model = model

    def get_queryset(self) -> "QuerySet":
        """Get a new queryset for the model."""
        if not self.model:
            raise ValueError("Manager must be associated with a model")
        return QuerySet(self.model)

    def all(self) -> "QuerySet":
        """Get all instances of the model."""
        return self.get_queryset()

    def filter(self, *args: Any, **kwargs: Any) -> "QuerySet":
        """Filter the queryset."""
        return self.get_queryset().filter(*args, **kwargs)

    def exclude(self, *args: Any, **kwargs: Any) -> "QuerySet":
        """Exclude from the queryset."""
        return self.get_queryset().exclude(*args, **kwargs)

    def get(self, *args: Any, **kwargs: Any) -> "QuerySet":
        """Get a single instance."""
        return self.get_queryset().get(*args, **kwargs)

    def first(self) -> "QuerySet":
        """Get the first instance."""
        return self.get_queryset().first()

    def last(self) -> "QuerySet":
        """Get the last instance."""
        return self.get_queryset().last()

    def count(self) -> "QuerySet":
        """Count instances."""
        return self.get_queryset().count()

    def exists(self) -> "QuerySet":
        """Check if any instances exist."""
        return self.get_queryset().exists()

    def create(self, **kwargs: Any) -> MODEL:
        """Create a new instance."""
        if not self.model:
            raise ValueError("Manager must be associated with a model")
        return self.model.create(**kwargs)

    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs: Any) -> tuple[MODEL, bool]:
        """Get an existing instance or create a new one."""
        if not self.model:
            raise ValueError("Manager must be associated with a model")
        return self.model.get_or_create(defaults=defaults, **kwargs)

    def update_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs: Any) -> tuple[MODEL, bool]:
        """Update an existing instance or create a new one."""
        if not self.model:
            raise ValueError("Manager must be associated with a model")
        return self.model.update_or_create(defaults=defaults, **kwargs)

    def bulk_create(self, objects: List[MODEL], batch_size: Optional[int] = None, **kwargs: Any) -> "QuerySet":
        """Bulk create objects."""
        return self.get_queryset().bulk_create(objects, batch_size=batch_size, **kwargs)

    def bulk_update(self, objects: List[MODEL], fields: List[str], batch_size: Optional[int] = None) -> "QuerySet":
        """Bulk update objects."""
        return self.get_queryset().bulk_update(objects, fields, batch_size=batch_size)

    def values(self, *fields: str, **named_fields: str) -> "QuerySet":
        """Return values as dictionaries."""
        return self.get_queryset().values(*fields, **named_fields)

    def values_list(self, *fields: str, flat: bool = False) -> "QuerySet":
        """Return values as lists."""
        return self.get_queryset().values_list(*fields, flat=flat)

    def distinct(self) -> "QuerySet":
        """Make the queryset distinct."""
        return self.get_queryset().distinct()

    def order_by(self, *field_names: str) -> "QuerySet":
        """Order the queryset."""
        return self.get_queryset().order_by(*field_names)

    def select_related(self, *field_names: str) -> "QuerySet":
        """Select related objects."""
        return self.get_queryset().select_related(*field_names)

    def prefetch_related(self, *lookups: Any) -> "QuerySet":
        """Prefetch related objects."""
        return self.get_queryset().prefetch_related(*lookups)

    def only(self, *field_names: str) -> "QuerySet":
        """Select only specific fields."""
        return self.get_queryset().only(*field_names)

    def defer(self, *field_names: str) -> "QuerySet":
        """Defer specific fields."""
        return self.get_queryset().defer(*field_names)

    def using(self, alias: str) -> "QuerySet":
        """Use a specific database."""
        return self.get_queryset().using_db(alias)

    def raw(self, raw_query: str, params: Optional[tuple] = None, translations: Optional[Dict[str, str]] = None) -> "QuerySet":
        """Execute raw SQL."""
        return self.get_queryset().raw(raw_query)

    def none(self) -> "QuerySet":
        """Return an empty queryset."""
        queryset = self.get_queryset()
        queryset._limit = 0
        return queryset

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to the queryset."""
        return getattr(self.get_queryset(), name)


class ManagerDescriptor:
    """
    Descriptor that provides access to the manager.
    
    This is used to make the manager accessible as a class attribute on models.
    """

    def __init__(self, manager_class: Type[Manager] = Manager):
        """Initialize the descriptor."""
        self.manager_class = manager_class
        self.manager = None

    def __get__(self, instance: Optional["Model"], owner: Optional[Type["Model"]] = None) -> "Manager":
        """Get the manager instance."""
        if instance is not None:
            # Called on an instance
            raise AttributeError("Manager isn't accessible via model instances.")

        if owner is None:
            raise AttributeError("Manager isn't accessible without a model class.")

        if self.manager is None:
            self.manager = self.manager_class(owner)

        return self.manager

    def __set__(self, instance: Optional["Model"], value: Any) -> None:
        """Set the manager (not allowed)."""
        raise AttributeError("Can't set the manager attribute.")


class DefaultManager(Manager):
    """
    Default manager for models.
    
    This is the manager that is automatically created for each model.
    """

    def __init__(self, model: Optional[Type["Model"]] = None):
        """Initialize the default manager."""
        super().__init__(model)

    def get_queryset(self) -> "QuerySet":
        """Get a new queryset for the model."""
        queryset = super().get_queryset()
        
        # Apply default ordering if specified
        if self.model and hasattr(self.model._meta, 'ordering') and self.model._meta.ordering:
            queryset = queryset.order_by(*self.model._meta.ordering)
        
        return queryset


# Create a default manager descriptor
objects = ManagerDescriptor(DefaultManager) 