"""
QuerySet and Q classes for OxenORM

This module provides the QuerySet class for building and executing queries,
and the Q class for complex query expressions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, Union
from .models import Model
from .rust_bridge import OxenEngine


class Q:
    """
    Q objects for complex query expressions.
    
    This allows building complex WHERE clauses with AND, OR, and NOT operations.
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.children = list(args)
        self.connector = "AND"
        self.negated = False
        
        # Add keyword arguments as equality conditions
        for key, value in kwargs.items():
            self.children.append((key, "=", value))
    
    def __and__(self, other: Q) -> Q:
        """Combine two Q objects with AND."""
        return self._combine(other, "AND")
    
    def __or__(self, other: Q) -> Q:
        """Combine two Q objects with OR."""
        return self._combine(other, "OR")
    
    def __invert__(self) -> Q:
        """Negate a Q object."""
        obj = Q()
        obj.add(self, "AND")
        obj.negated = True
        return obj
    
    def _combine(self, other: Q, conn: str) -> Q:
        """Combine this Q object with another using the specified connector."""
        if self.connector == conn and not self.negated:
            obj = Q()
            obj.connector = conn
            obj.children = self.children + other.children
            return obj
        else:
            obj = Q()
            obj.add(self, conn)
            obj.add(other, conn)
            return obj
    
    def add(self, q_object: Q, conn_type: str) -> None:
        """Add a Q object to this one."""
        if self.connector == conn_type and not self.negated:
            self.children.extend(q_object.children)
        else:
            obj = Q()
            obj.connector = conn_type
            obj.children = [self, q_object]
            self.connector = obj.connector
            self.children = obj.children
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Q object to a dictionary for the Rust backend."""
        if not self.children:
            return {}
        
        if len(self.children) == 1 and isinstance(self.children[0], tuple):
            # Single condition
            key, op, value = self.children[0]
            return {key: value}
        
        # Complex conditions - for now, flatten to simple conditions
        # In a full implementation, this would handle complex logic
        result = {}
        for child in self.children:
            if isinstance(child, tuple):
                key, op, value = child
                result[key] = value
            elif isinstance(child, Q):
                result.update(child.to_dict())
        
        return result


class QuerySet:
    """
    QuerySet for building and executing database queries.
    
    This provides a fluent interface for building complex queries
    and delegates execution to the Rust backend.
    """
    
    def __init__(self, model_class: Type[Model]) -> None:
        self.model_class = model_class
        self._conditions: Dict[str, Any] = {}
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._order_by: List[str] = []
        self._select_fields: List[str] = []
        self._distinct: bool = False
    
    def filter(self, *args: Q, **kwargs: Any) -> QuerySet:
        """Filter the queryset by conditions."""
        qs = self._clone()
        
        # Handle Q objects
        for q_obj in args:
            qs._conditions.update(q_obj.to_dict())
        
        # Handle keyword arguments
        qs._conditions.update(kwargs)
        
        return qs
    
    def exclude(self, *args: Q, **kwargs: Any) -> QuerySet:
        """Exclude records matching conditions."""
        # For now, implement as simple filtering
        # In a full implementation, this would handle NOT logic
        qs = self._clone()
        
        # Handle Q objects
        for q_obj in args:
            qs._conditions.update(q_obj.to_dict())
        
        # Handle keyword arguments
        qs._conditions.update(kwargs)
        
        return qs
    
    def order_by(self, *fields: str) -> QuerySet:
        """Order the queryset by fields."""
        qs = self._clone()
        qs._order_by.extend(fields)
        return qs
    
    def reverse(self) -> QuerySet:
        """Reverse the ordering of the queryset."""
        qs = self._clone()
        qs._order_by = [f"-{field}" if not field.startswith('-') else field[1:] 
                       for field in reversed(qs._order_by)]
        return qs
    
    def limit(self, limit: int) -> QuerySet:
        """Limit the number of results."""
        qs = self._clone()
        qs._limit = limit
        return qs
    
    def offset(self, offset: int) -> QuerySet:
        """Offset the results."""
        qs = self._clone()
        qs._offset = offset
        return qs
    
    def select(self, *fields: str) -> QuerySet:
        """Select specific fields."""
        qs = self._clone()
        qs._select_fields.extend(fields)
        return qs
    
    def distinct(self) -> QuerySet:
        """Return distinct results."""
        qs = self._clone()
        qs._distinct = True
        return qs
    
    async def get(self, **kwargs: Any) -> Model:
        """Get a single object matching the criteria."""
        qs = self.filter(**kwargs)
        qs._limit = 1
        
        results = await qs._execute()
        if not results:
            raise self.model_class.DoesNotExist(
                f"{self.model_class.__name__} matching query does not exist."
            )
        if len(results) > 1:
            raise self.model_class.MultipleObjectsReturned(
                f"get() returned more than one {self.model_class.__name__} -- it returned {len(results)}!"
            )
        
        return results[0]
    
    async def first(self) -> Optional[Model]:
        """Get the first object matching the criteria."""
        qs = self._clone()
        qs._limit = 1
        
        results = await qs._execute()
        return results[0] if results else None
    
    async def last(self) -> Optional[Model]:
        """Get the last object matching the criteria."""
        qs = self._clone()
        qs._limit = 1
        
        # Add reverse ordering if no ordering is specified
        if not qs._order_by:
            qs._order_by = [f"-{self.model_class._meta.pk_attr}"]
        else:
            qs = qs.reverse()
        
        results = await qs._execute()
        return results[0] if results else None
    
    async def count(self) -> int:
        """Count the number of objects matching the criteria."""
        engine = await self._get_engine()
        table_name = self.model_class._meta.table or self.model_class.__name__.lower()
        
        return await engine.count_models(table_name, self._conditions)
    
    async def exists(self) -> bool:
        """Check if any objects match the criteria."""
        return await self.count() > 0
    
    async def all(self) -> List[Model]:
        """Get all objects matching the criteria."""
        return await self._execute()
    
    async def __aiter__(self):
        """Async iterator for the queryset."""
        results = await self._execute()
        for result in results:
            yield result
    
    async def __await__(self):
        """Await the queryset to get all results."""
        return await self._execute()
    
    def _clone(self) -> QuerySet:
        """Create a copy of this queryset."""
        qs = QuerySet(self.model_class)
        qs._conditions = self._conditions.copy()
        qs._limit = self._limit
        qs._offset = self._offset
        qs._order_by = self._order_by.copy()
        qs._select_fields = self._select_fields.copy()
        qs._distinct = self._distinct
        return qs
    
    async def _get_engine(self) -> OxenEngine:
        """Get the Rust engine instance."""
        return await self.model_class._get_rust_engine()
    
    async def _execute(self) -> List[Model]:
        """Execute the query using the Rust backend."""
        engine = await self._get_engine()
        table_name = self.model_class._meta.table or self.model_class.__name__.lower()
        
        results = await engine.query_models(
            table_name=table_name,
            conditions=self._conditions,
            limit=self._limit,
            offset=self._offset,
            order_by=self._order_by,
            pk_field=self.model_class._meta.pk_attr
        )
        
        # Convert results to model instances
        return [self.model_class(**result) for result in results]
    
    def __repr__(self) -> str:
        return f"<QuerySet [{self.model_class.__name__}]>" 