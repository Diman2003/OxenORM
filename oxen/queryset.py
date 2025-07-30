#!/usr/bin/env python3
"""
OxenORM QuerySet System

This module provides the core queryset functionality for OxenORM,
inspired by Tortoise ORM but optimized for OxenORM's architecture.
"""

import asyncio
from collections.abc import AsyncIterator, Callable, Collection, Generator, Iterable
from copy import copy
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar, cast, overload, Literal
from dataclasses import dataclass, field
from enum import Enum

from oxen.exceptions import (
    DoesNotExist, FieldError, IntegrityError, MultipleObjectsReturned,
    ParamsError, ValidationError, OperationalError
)
from oxen.expressions import Expression, Q, RawSQL, ResolveContext, ResolveResult
from oxen.fields.relational import (
    ForeignKeyField, OneToOneField, RelationalField
)
from oxen.filters import FilterInfoDict
from oxen.query_utils import (
    Prefetch, QueryModifier, TableCriterionTuple,
    expand_lookup_expression, get_joins_for_related_field
)

if TYPE_CHECKING:  # pragma: nocoverage
    from oxen.models import Model

MODEL = TypeVar("MODEL", bound="Model")
T_co = TypeVar("T_co", covariant=True)
SINGLE = TypeVar("SINGLE", bound=bool)


class Order(str, Enum):
    """Ordering direction."""
    ASC = "ASC"
    DESC = "DESC"


class QuerySetSingle(Generic[T_co]):
    """
    Awaitable query that resolves to a single instance of the Model object.
    """
    
    def __init__(self, queryset: 'QuerySet[T_co]'):
        self.queryset = queryset
    
    def __await__(self) -> Generator[Any, None, T_co]:
        """Make the queryset awaitable."""
        async def _self() -> T_co:
            results = await self.queryset._execute()
            if self.queryset._single:
                if not results and hasattr(self.queryset, '_raise_does_not_exist') and self.queryset._raise_does_not_exist:
                    raise DoesNotExist(f"No {self.queryset.model.__name__} matches the given query.")
                return results[0] if results else None
            else:
                return results[0] if results else None
        return _self().__await__()

    def prefetch_related(
        self, *args: str | Prefetch
    ) -> 'QuerySetSingle[T_co]':
        """Prefetch related objects."""
        raise NotImplementedError()

    def select_related(self, *args: str) -> 'QuerySetSingle[T_co]':
        """Select related objects."""
        raise NotImplementedError()

    def annotate(
        self, **kwargs: Expression
    ) -> 'QuerySetSingle[T_co]':
        """Add annotations to the query."""
        raise NotImplementedError()

    def only(self, *fields_for_select: str) -> 'QuerySetSingle[T_co]':
        """Select only specific fields."""
        raise NotImplementedError()

    def values_list(
        self, *fields_: str, flat: bool = False
    ) -> 'ValuesListQuery[Literal[True]]':
        """Return values as a list."""
        raise NotImplementedError()

    def values(
        self, *args: str, **kwargs: str
    ) -> 'ValuesQuery[Literal[True]]':
        """Return values as dictionaries."""
        raise NotImplementedError()


class AwaitableQuery(Generic[MODEL]):
    """Base class for awaitable queries."""
    
    __slots__ = (
        "query",
        "model",
        "_joined_tables",
        "_db",
        "capabilities",
        "_annotations",
        "_custom_filters",
        "_q_objects",
    )

    def __init__(self, model: type[MODEL]) -> None:
        """Initialize the query."""
        self._joined_tables: list = []
        self.model: type[MODEL] = model
        self.query: str = ""
        self._db: Any = None
        self.capabilities: Any = None
        self._annotations: dict[str, Expression] = {}
        self._custom_filters: dict[str, FilterInfoDict] = {}
        self._q_objects: list[Q] = []

    def _choose_db(self, for_write: bool = False) -> Any:
        """Choose database connection."""
        if self._db is None:
            self._db = self.model._meta.db
        return self._db

    def _choose_db_if_not_chosen(self, for_write: bool = False) -> None:
        """Choose database if not already chosen."""
        if self._db is None:
            self._choose_db(for_write)

    def resolve_filters(self) -> None:
        """Resolve filters to SQL."""
        # This would be implemented with actual SQL generation
        pass

    def _join_table_by_field(
        self, table: str, related_field_name: str, related_field: RelationalField
    ) -> str:
        """Join table by field."""
        # This would be implemented with actual JOIN logic
        return table

    def _join_table(self, table_criterion_tuple: TableCriterionTuple) -> None:
        """Join table with criteria."""
        # This would be implemented with actual JOIN logic
        pass

    @staticmethod
    def _resolve_ordering_string(ordering: str, reverse: bool = False) -> tuple[str, Order]:
        """Resolve ordering string to field and direction."""
        if ordering.startswith('-'):
            return ordering[1:], Order.DESC
        return ordering, Order.ASC

    def resolve_ordering(
        self,
        model: type['Model'],
        table: str,
        orderings: Iterable[tuple[str, str | Order]],
        annotations: dict[str, Any],
        fields_for_select: Collection[str] | None = None,
    ) -> None:
        """Resolve ordering to SQL."""
        # This would be implemented with actual ORDER BY logic
        pass

    def _resolve_annotate(self) -> bool:
        """Resolve annotations to SQL."""
        # This would be implemented with actual annotation logic
        return bool(self._annotations)

    def sql(self, params_inline: bool = False) -> str:
        """Generate SQL for the query."""
        # This would be implemented with actual SQL generation
        return self.query

    def _make_query(self) -> None:
        """Build the query."""
        # This would be implemented with actual query building
        pass

    async def _execute(self) -> Any:
        """Execute the query."""
        # This would be implemented with actual database execution
        pass


class QuerySet(AwaitableQuery[MODEL]):
    """
    QuerySet for model operations.
    
    This class provides methods for building and executing queries
    against the database.
    """

    __slots__ = (
        "_limit",
        "_offset",
        "_distinct",
        "_orderings",
        "_force_indexes",
        "_use_indexes",
        "_only_fields",
        "_select_related",
        "_prefetch_related",
        "_group_bys",
        "_having",
        "_single",
        "_raise_does_not_exist",
    )

    def __init__(self, model: type[MODEL], db: Any = None) -> None:
        """Initialize the queryset."""
        super().__init__(model)
        self._db = db
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._distinct: bool = False
        self._orderings: list[tuple[str, Order]] = []
        self._force_indexes: set[str] = set()
        self._use_indexes: set[str] = set()
        self._only_fields: Optional[tuple[str, ...]] = None
        self._select_related: set[str] = set()
        self._prefetch_related: list[Prefetch] = []
        self._group_bys: tuple[str, ...] = ()
        self._having: Optional[Q] = None
        self._single: bool = False
        self._raise_does_not_exist: bool = True

    def _clone(self) -> 'QuerySet[MODEL]':
        """Clone the queryset."""
        clone = self.__class__(self.model, self._db)
        clone._limit = self._limit
        clone._offset = self._offset
        clone._distinct = self._distinct
        clone._orderings = self._orderings.copy()
        clone._force_indexes = self._force_indexes.copy()
        clone._use_indexes = self._use_indexes.copy()
        clone._only_fields = self._only_fields
        clone._select_related = self._select_related.copy()
        clone._prefetch_related = self._prefetch_related.copy()
        clone._group_bys = self._group_bys
        clone._having = self._having
        clone._single = self._single
        clone._raise_does_not_exist = self._raise_does_not_exist
        clone._annotations = self._annotations.copy()
        clone._custom_filters = self._custom_filters.copy()
        clone._q_objects = self._q_objects.copy()
        return clone

    def _filter_or_exclude(self, *args: Q, negate: bool, **kwargs: Any) -> 'QuerySet[MODEL]':
        """Filter or exclude based on criteria."""
        clone = self._clone()
        
        # Add Q objects
        for q_obj in args:
            clone._q_objects.append(q_obj)
        
        # Add keyword filters
        for key, value in kwargs.items():
            q_obj = Q(**{key: value})
            clone._q_objects.append(q_obj)
        
        return clone

    def filter(self, *args: Q, **kwargs: Any) -> 'QuerySet[MODEL]':
        """Filter the queryset."""
        return self._filter_or_exclude(*args, negate=False, **kwargs)

    def exclude(self, *args: Q, **kwargs: Any) -> 'QuerySet[MODEL]':
        """Exclude from the queryset."""
        return self._filter_or_exclude(*args, negate=True, **kwargs)

    def _parse_orderings(
        self, orderings: tuple[str, ...], reverse: bool = False
    ) -> list[tuple[str, Order]]:
        """Parse ordering strings."""
        parsed_orderings = []
        for ordering in orderings:
            field, direction = self._resolve_ordering_string(ordering, reverse)
            parsed_orderings.append((field, direction))
        return parsed_orderings

    def order_by(self, *orderings: str) -> 'QuerySet[MODEL]':
        """Order the queryset."""
        clone = self._clone()
        clone._orderings.extend(self._parse_orderings(orderings))
        return clone

    def _as_single(self) -> QuerySetSingle[MODEL | None]:
        """Convert to single result queryset."""
        clone = self._clone()
        clone._single = True
        return QuerySetSingle(clone)

    def latest(self, *orderings: str) -> QuerySetSingle[MODEL | None]:
        """Get the latest record."""
        if not orderings:
            orderings = (self.model._meta.pk_attr,)
        
        clone = self._clone()
        clone._orderings.extend(self._parse_orderings(orderings, reverse=True))
        clone._limit = 1
        clone._single = True
        return QuerySetSingle(clone)

    def earliest(self, *orderings: str) -> QuerySetSingle[MODEL | None]:
        """Get the earliest record."""
        if not orderings:
            orderings = (self.model._meta.pk_attr,)
        
        clone = self._clone()
        clone._orderings.extend(self._parse_orderings(orderings))
        clone._limit = 1
        clone._single = True
        return QuerySetSingle(clone)

    def limit(self, limit: int) -> 'QuerySet[MODEL]':
        """Limit the number of results."""
        clone = self._clone()
        clone._limit = limit
        return clone

    def offset(self, offset: int) -> 'QuerySet[MODEL]':
        """Offset the results."""
        clone = self._clone()
        clone._offset = offset
        return clone

    def __getitem__(self, key: slice) -> 'QuerySet[MODEL]':
        """Get a slice of results."""
        clone = self._clone()
        
        if key.start is not None:
            clone._offset = key.start
        
        if key.stop is not None:
            if key.start is not None:
                clone._limit = key.stop - key.start
            else:
                clone._limit = key.stop
        
        return clone

    def distinct(self) -> 'QuerySet[MODEL]':
        """Make the queryset distinct."""
        clone = self._clone()
        clone._distinct = True
        return clone

    def select_for_update(
        self,
        nowait: bool = False,
        skip_locked: bool = False,
        of: tuple[str, ...] = (),
        no_key: bool = False,
    ) -> 'QuerySet[MODEL]':
        """Select for update with locking."""
        clone = self._clone()
        # This would be implemented with actual SELECT FOR UPDATE logic
        return clone

    def annotate(self, **kwargs: Expression) -> 'QuerySet[MODEL]':
        """Add annotations to the query."""
        clone = self._clone()
        clone._annotations.update(kwargs)
        return clone

    def group_by(self, *fields: str) -> 'QuerySet[MODEL]':
        """Group by fields."""
        clone = self._clone()
        clone._group_bys = fields
        return clone

    def having(self, *args: Q, **kwargs: Any) -> 'QuerySet[MODEL]':
        """Add HAVING clause."""
        clone = self._clone()
        if args:
            clone._having = args[0]
        else:
            clone._having = Q(**kwargs)
        return clone

    def values_list(self, *fields_: str, flat: bool = False) -> 'ValuesListQuery[Literal[False]]':
        """Return values as a list."""
        return ValuesListQuery(
            model=self.model,
            db=self._db,
            q_objects=self._q_objects,
            single=False,
            raise_does_not_exist=self._raise_does_not_exist,
            fields_for_select_list=fields_,
            limit=self._limit,
            offset=self._offset,
            distinct=self._distinct,
            orderings=self._orderings,
            flat=flat,
            annotations=self._annotations,
            custom_filters=self._custom_filters,
            group_bys=self._group_bys,
            force_indexes=self._force_indexes,
            use_indexes=self._use_indexes,
        )

    def values(self, *args: str, **kwargs: str) -> 'ValuesQuery[Literal[False]]':
        """Return values as dictionaries."""
        return ValuesQuery(
            model=self.model,
            db=self._db,
            q_objects=self._q_objects,
            single=False,
            raise_does_not_exist=self._raise_does_not_exist,
            fields_for_select=kwargs,
            limit=self._limit,
            offset=self._offset,
            distinct=self._distinct,
            orderings=self._orderings,
            annotations=self._annotations,
            custom_filters=self._custom_filters,
            group_bys=self._group_bys,
            force_indexes=self._force_indexes,
            use_indexes=self._use_indexes,
        )

    def delete(self) -> 'DeleteQuery':
        """Delete matching records."""
        return DeleteQuery(
            model=self.model,
            db=self._db,
            q_objects=self._q_objects
        )

    def update(self, **kwargs: Any) -> 'UpdateQuery':
        """Update matching records."""
        return UpdateQuery(
            model=self.model,
            update_kwargs=kwargs,
            db=self._db,
            q_objects=self._q_objects,
            annotations=self._annotations,
            custom_filters=self._custom_filters,
            limit=self._limit,
            orderings=self._orderings,
        )

    def count(self) -> 'CountQuery':
        """Count matching records."""
        return CountQuery(
            model=self.model,
            db=self._db,
            q_objects=self._q_objects,
            annotations=self._annotations,
            custom_filters=self._custom_filters,
            force_indexes=self._force_indexes,
            use_indexes=self._use_indexes,
        )

    def exists(self) -> 'ExistsQuery':
        """Check if any records exist."""
        return ExistsQuery(
            model=self.model,
            db=self._db,
            q_objects=self._q_objects,
            annotations=self._annotations,
            custom_filters=self._custom_filters,
            force_indexes=self._force_indexes,
            use_indexes=self._use_indexes,
        )

    def all(self) -> 'QuerySet[MODEL]':
        """Get all records."""
        return self._clone()

    def raw(self, sql: str) -> 'RawSQLQuery':
        """Execute raw SQL."""
        return RawSQLQuery(self.model, self._db, sql)

    def first(self) -> QuerySetSingle[MODEL | None]:
        """Get the first record."""
        clone = self._clone()
        clone._limit = 1
        clone._single = True
        clone._raise_does_not_exist = False
        return QuerySetSingle(clone)

    def last(self) -> QuerySetSingle[MODEL | None]:
        """Get the last record."""
        clone = self._clone()
        if not clone._orderings:
            clone._orderings = [(self.model._meta.pk_attr, Order.DESC)]
        clone._limit = 1
        clone._single = True
        clone._raise_does_not_exist = False
        return QuerySetSingle(clone)

    def get(self, *args: Q, **kwargs: Any) -> QuerySetSingle[MODEL]:
        """Get a single record."""
        clone = self._clone()
        
        # Add filter criteria
        for q_obj in args:
            clone._q_objects.append(q_obj)
        for key, value in kwargs.items():
            clone._q_objects.append(Q(**{key: value}))
        
        clone._limit = 1
        clone._single = True
        clone._raise_does_not_exist = True
        return QuerySetSingle(clone)

    async def in_bulk(self, id_list: Iterable[str | int], field_name: str = "pk") -> dict[str, MODEL]:
        """Get multiple records by ID."""
        if not id_list:
            return {}
        
        # Build filter for the IDs
        filter_kwargs = {f"{field_name}__in": list(id_list)}
        queryset = self.filter(**filter_kwargs)
        
        # Execute query and build result dict
        results = await queryset
        return {str(getattr(obj, field_name)): obj for obj in results}

    def bulk_create(
        self,
        objects: Iterable[MODEL],
        batch_size: Optional[int] = None,
        ignore_conflicts: bool = False,
        update_fields: Optional[Iterable[str]] = None,
        on_conflict: Optional[Iterable[str]] = None,
    ) -> 'BulkCreateQuery[MODEL]':
        """Bulk create objects."""
        return BulkCreateQuery(
            model=self.model,
            db=self._db,
            objects=objects,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_fields=update_fields,
            on_conflict=on_conflict,
        )

    def bulk_update(
        self,
        objects: Iterable[MODEL],
        fields: Iterable[str],
        batch_size: Optional[int] = None,
    ) -> 'BulkUpdateQuery[MODEL]':
        """Bulk update objects."""
        return BulkUpdateQuery(
            model=self.model,
            db=self._db,
            q_objects=self._q_objects,
            annotations=self._annotations,
            custom_filters=self._custom_filters,
            limit=self._limit,
            orderings=self._orderings,
            objects=objects,
            fields=fields,
            batch_size=batch_size,
        )

    def get_or_none(self, *args: Q, **kwargs: Any) -> QuerySetSingle[MODEL | None]:
        """Get a single record or None."""
        clone = self._clone()
        
        # Add filter criteria
        for q_obj in args:
            clone._q_objects.append(q_obj)
        for key, value in kwargs.items():
            clone._q_objects.append(Q(**{key: value}))
        
        clone._limit = 1
        clone._single = True
        clone._raise_does_not_exist = False
        return QuerySetSingle(clone)

    def only(self, *fields_for_select: str) -> 'QuerySet[MODEL]':
        """Select only specific fields."""
        clone = self._clone()
        clone._only_fields = fields_for_select
        return clone

    def select_related(self, *fields: str) -> 'QuerySet[MODEL]':
        """Select related objects."""
        clone = self._clone()
        clone._select_related.update(fields)
        return clone

    def force_index(self, *index_names: str) -> 'QuerySet[MODEL]':
        """Force use of specific indexes."""
        clone = self._clone()
        clone._force_indexes.update(index_names)
        return clone

    def use_index(self, *index_names: str) -> 'QuerySet[MODEL]':
        """Use specific indexes."""
        clone = self._clone()
        clone._use_indexes.update(index_names)
        return clone

    def prefetch_related(self, *args: str | Prefetch) -> 'QuerySet[MODEL]':
        """Prefetch related objects."""
        clone = self._clone()
        for arg in args:
            if isinstance(arg, str):
                clone._prefetch_related.append(Prefetch(arg))
            else:
                clone._prefetch_related.append(arg)
        return clone

    async def explain(self) -> Any:
        """Explain the query execution plan."""
        # This would be implemented with actual EXPLAIN logic
        pass

    def using_db(self, _db: Any) -> 'QuerySet[MODEL]':
        """Use a specific database connection."""
        clone = self._clone()
        clone._db = _db
        return clone

    def _join_select_related(self, lookup_expression: str) -> tuple[type['Model'], str]:
        """Join for select_related."""
        # This would be implemented with actual JOIN logic
        return self.model, ""

    def _resolve_only(self, only_lookup_expressions: tuple[str, ...]) -> None:
        """Resolve only fields."""
        # This would be implemented with actual field resolution
        pass

    def _make_query(self) -> None:
        """Build the query."""
        # This would be implemented with actual query building
        pass

    def __await__(self) -> Generator[Any, None, list[MODEL]]:
        """Make the queryset awaitable."""
        async def _self() -> list[MODEL]:
            return await self._execute()
        return _self().__await__()

    async def __aiter__(self) -> AsyncIterator[MODEL]:
        """Async iterator over results."""
        results = await self._execute()
        for result in results:
            yield result

    async def _execute(self) -> list[MODEL]:
        """Execute the query and return results."""
        # Get database connection
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")
        
        # Build conditions from filters
        conditions = {}
        for q_obj in self._q_objects:
            # Handle Q objects properly
            if hasattr(q_obj, 'filters'):
                conditions.update(q_obj.filters)
            elif hasattr(q_obj, 'children'):
                for child in q_obj.children:
                    if hasattr(child, 'filters'):
                        conditions.update(child.filters)
                    elif isinstance(child, dict):
                        conditions.update(child)
            elif isinstance(q_obj, dict):
                conditions.update(q_obj)
            else:
                # Try to convert to dict
                try:
                    conditions.update(dict(q_obj))
                except:
                    # Skip if can't convert
                    pass
        
        # Build the query
        query = f"SELECT * FROM {self.model._meta.table_name}"
        params = []
        
        # Add WHERE clause if conditions exist
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                # Handle field lookups like age__lt
                if '__' in key:
                    field_name, lookup = key.split('__', 1)
                    if lookup == 'lt':
                        where_clauses.append(f"{field_name} < ?")
                        params.append(value)
                    elif lookup == 'lte':
                        where_clauses.append(f"{field_name} <= ?")
                        params.append(value)
                    elif lookup == 'gt':
                        where_clauses.append(f"{field_name} > ?")
                        params.append(value)
                    elif lookup == 'gte':
                        where_clauses.append(f"{field_name} >= ?")
                        params.append(value)
                    elif lookup == 'startswith':
                        where_clauses.append(f"{field_name} LIKE ?")
                        params.append(f"{value}%")
                    elif lookup == 'endswith':
                        where_clauses.append(f"{field_name} LIKE ?")
                        params.append(f"%{value}")
                    elif lookup == 'contains':
                        where_clauses.append(f"{field_name} LIKE ?")
                        params.append(f"%{value}%")
                    elif lookup == 'in':
                        if isinstance(value, (list, tuple)):
                            placeholders = ', '.join(['?' for _ in value])
                            where_clauses.append(f"{field_name} IN ({placeholders})")
                            params.extend(value)
                        else:
                            where_clauses.append(f"{field_name} IN (?)")
                            params.append(value)
                    else:
                        # Unknown lookup, treat as exact match
                        where_clauses.append(f"{field_name} = ?")
                        params.append(value)
                else:
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        # Add ORDER BY clause
        if self._orderings:
            order_clauses = []
            for field, direction in self._orderings:
                order_clauses.append(f"{field} {direction.value}")
            query += " ORDER BY " + ", ".join(order_clauses)
        
        # Add LIMIT clause
        if self._limit is not None:
            query += f" LIMIT {self._limit}"
        
        # Add OFFSET clause
        if self._offset is not None:
            query += f" OFFSET {self._offset}"
        
        # Execute the query
        result = await db.execute_query(query, params if params else None)
        
        if result.get('error') is None:
            records = result.get('data', [])
            instances = []
            for record in records:
                instance = self.model._init_from_db(**record)
                instance._meta.db = db
                instances.append(instance)
            return instances
        else:
            raise OperationalError(f"Failed to execute query: {result.get('error', 'Unknown error')}")


# Placeholder classes for other query types
class UpdateQuery(AwaitableQuery):
    """Query for updating records."""
    pass

class DeleteQuery(AwaitableQuery):
    """Query for deleting records."""
    
    def __init__(self, model: type[MODEL], db: Any = None, q_objects: list[Q] = None):
        super().__init__(model)
        self._db = db
        self._q_objects = q_objects or []
    
    def __await__(self) -> Generator[Any, None, int]:
        """Make the delete query awaitable."""
        async def _self() -> int:
            return await self._execute()
        return _self().__await__()
    
    async def _execute(self) -> int:
        """Execute the delete query and return the number of deleted records."""
        # Get database connection
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")
        
        # Build conditions from filters
        conditions = {}
        for q_obj in self._q_objects:
            # Handle Q objects properly
            if hasattr(q_obj, 'filters'):
                # This is a Q object with filters
                conditions.update(q_obj.filters)
            elif hasattr(q_obj, 'children'):
                # This is a Q object with children
                for child in q_obj.children:
                    if hasattr(child, 'filters'):
                        conditions.update(child.filters)
                    elif isinstance(child, dict):
                        conditions.update(child)
            elif isinstance(q_obj, dict):
                # This is a simple dict
                conditions.update(q_obj)
            else:
                # Try to convert to dict
                try:
                    conditions.update(dict(q_obj))
                except:
                    # Skip if can't convert
                    pass
        
        # Build the DELETE query with proper field lookup processing
        query = f"DELETE FROM {self.model._meta.table_name}"
        params = []
        
        # Add WHERE clause if conditions exist
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                # Handle field lookups like age__lt
                if '__' in key:
                    field_name, lookup = key.split('__', 1)
                    if lookup == 'lt':
                        where_clauses.append(f"{field_name} < ?")
                        params.append(value)
                    elif lookup == 'lte':
                        where_clauses.append(f"{field_name} <= ?")
                        params.append(value)
                    elif lookup == 'gt':
                        where_clauses.append(f"{field_name} > ?")
                        params.append(value)
                    elif lookup == 'gte':
                        where_clauses.append(f"{field_name} >= ?")
                        params.append(value)
                    elif lookup == 'startswith':
                        where_clauses.append(f"{field_name} LIKE ?")
                        params.append(f"{value}%")
                    elif lookup == 'endswith':
                        where_clauses.append(f"{field_name} LIKE ?")
                        params.append(f"%{value}")
                    elif lookup == 'contains':
                        where_clauses.append(f"{field_name} LIKE ?")
                        params.append(f"%{value}%")
                    elif lookup == 'in':
                        if isinstance(value, (list, tuple)):
                            placeholders = ', '.join(['?' for _ in value])
                            where_clauses.append(f"{field_name} IN ({placeholders})")
                            params.extend(value)
                        else:
                            where_clauses.append(f"{field_name} IN (?)")
                            params.append(value)
                    else:
                        # Unknown lookup, treat as exact match
                        where_clauses.append(f"{field_name} = ?")
                        params.append(value)
                else:
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        # Execute the delete query
        result = await db.execute_query(query, params if params else None)
        
        if result.get('error') is None:
            return result.get('rows_affected', 0)
        else:
            raise OperationalError(f"Failed to execute delete query: {result.get('error', 'Unknown error')}")

class ExistsQuery(AwaitableQuery):
    """Query for checking existence."""
    
    def __await__(self) -> Generator[Any, None, bool]:
        """Make the exists query awaitable."""
        async def _self() -> bool:
            return await self._execute()
        return _self().__await__()
    
    async def _execute(self) -> bool:
        """Execute the exists query and return True if any records exist."""
        # Use count query with limit 1 for efficiency
        count_query = CountQuery(self.model, self._db)
        count_query._q_objects = self._q_objects
        count_query._limit = 1
        
        count = await count_query._execute()
        return count > 0

class CountQuery(AwaitableQuery):
    """Query for counting records."""
    
    def __init__(self, model: type[MODEL], db: Any = None, q_objects: list[Q] = None, 
                 annotations: dict[str, Any] = None, custom_filters: dict[str, Any] = None,
                 force_indexes: list[str] = None, use_indexes: list[str] = None):
        super().__init__(model)
        self._db = db
        self._q_objects = q_objects or []
        self._annotations = annotations or {}
        self._custom_filters = custom_filters or {}
        self._force_indexes = force_indexes or []
        self._use_indexes = use_indexes or []
    
    def __await__(self) -> Generator[Any, None, int]:
        """Make the count query awaitable."""
        async def _self() -> int:
            return await self._execute()
        return _self().__await__()
    
    async def _execute(self) -> int:
        """Execute the count query and return the count."""
        # Get database connection
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")
        
        # Build conditions from filters
        conditions = {}
        for q_obj in self._q_objects:
            # Handle Q objects properly
            if hasattr(q_obj, 'filters'):
                # This is a Q object with filters
                conditions.update(q_obj.filters)
            elif hasattr(q_obj, 'children'):
                # This is a Q object with children
                for child in q_obj.children:
                    if hasattr(child, 'filters'):
                        conditions.update(child.filters)
                    elif isinstance(child, dict):
                        conditions.update(child)
            elif isinstance(q_obj, dict):
                # This is a simple dict
                conditions.update(q_obj)
            else:
                # Try to convert to dict
                try:
                    conditions.update(dict(q_obj))
                except:
                    # Skip if can't convert
                    pass
        
        # Build the count query
        query = f"SELECT COUNT(*) as count FROM {self.model._meta.table_name}"
        params = []
        
        # Add WHERE clause if conditions exist
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                # Handle field lookups like age__lt
                if '__' in key:
                    field_name, lookup = key.split('__', 1)
                    if lookup == 'lt':
                        where_clauses.append(f"{field_name} < ?")
                        params.append(value)
                    elif lookup == 'lte':
                        where_clauses.append(f"{field_name} <= ?")
                        params.append(value)
                    elif lookup == 'gt':
                        where_clauses.append(f"{field_name} > ?")
                        params.append(value)
                    elif lookup == 'gte':
                        where_clauses.append(f"{field_name} >= ?")
                        params.append(value)
                    elif lookup == 'in':
                        if isinstance(value, (list, tuple)):
                            placeholders = ', '.join(['?' for _ in value])
                            where_clauses.append(f"{field_name} IN ({placeholders})")
                            params.extend(value)
                        else:
                            where_clauses.append(f"{field_name} IN (?)")
                            params.append(value)
                    elif lookup == 'contains':
                        where_clauses.append(f"{field_name} LIKE ?")
                        params.append(f"%{value}%")
                    elif lookup == 'startswith':
                        where_clauses.append(f"{field_name} LIKE ?")
                        params.append(f"{value}%")
                    elif lookup == 'endswith':
                        where_clauses.append(f"{field_name} LIKE ?")
                        params.append(f"%{value}")
                    else:
                        # Unknown lookup, treat as exact match
                        where_clauses.append(f"{field_name} = ?")
                        params.append(value)
                else:
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
        
        # Execute the count query
        result = await db.execute_query(query, params if params else None)
        
        if result.get('error') is None:
            records = result.get('data', [])
            if records:
                return records[0].get('count', 0)
            return 0
        else:
            raise OperationalError(f"Failed to execute count query: {result.get('error', 'Unknown error')}")

class ValuesListQuery(AwaitableQuery, Generic[SINGLE]):
    """Query for returning values as lists."""
    pass

class ValuesQuery(AwaitableQuery, Generic[SINGLE]):
    """Query for returning values as dictionaries."""
    pass

class RawSQLQuery(AwaitableQuery):
    """Query for executing raw SQL."""
    pass

class BulkUpdateQuery(UpdateQuery, Generic[MODEL]):
    """Query for bulk updating objects."""
    pass

class BulkCreateQuery(AwaitableQuery, Generic[MODEL]):
    """Query for bulk creating objects."""
    
    def __init__(self, model: type[MODEL], db: Any = None, objects: Iterable[MODEL] = None, 
                 batch_size: Optional[int] = None, ignore_conflicts: bool = False,
                 update_fields: Optional[Iterable[str]] = None, on_conflict: Optional[Iterable[str]] = None):
        super().__init__(model)
        self._db = db
        self.objects = objects or []
        self.batch_size = batch_size
        self.ignore_conflicts = ignore_conflicts
        self.update_fields = update_fields
        self.on_conflict = on_conflict
    
    def __await__(self) -> Generator[Any, None, list[MODEL]]:
        """Make the bulk create query awaitable."""
        async def _self() -> list[MODEL]:
            return await self._execute()
        return _self().__await__()
    
    async def _execute(self) -> list[MODEL]:
        """Execute the bulk create query and return created objects."""
        # This would be implemented with actual database execution
        # For now, return the objects as-is
        return list(self.objects) 