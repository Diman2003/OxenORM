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
    from oxen.expressions import WindowFunction

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
        # Delegate to underlying queryset and preserve single semantics
        return QuerySetSingle(self.queryset.prefetch_related(*args))

    def select_related(self, *args: str) -> 'QuerySetSingle[T_co]':
        """Select related objects."""
        return QuerySetSingle(self.queryset.select_related(*args))

    def annotate(
        self, **kwargs: Expression
    ) -> 'QuerySetSingle[T_co]':
        """Add annotations to the query."""
        return QuerySetSingle(self.queryset.annotate(**kwargs))

    def only(self, *fields_for_select: str) -> 'QuerySetSingle[T_co]':
        """Select only specific fields."""
        return QuerySetSingle(self.queryset.only(*fields_for_select))

    def values_list(
        self, *fields_: str, flat: bool = False
    ) -> 'ValuesListQuery[Literal[True]]':
        """Return values as a list."""
        # Return a single-row values list query
        q = self.queryset.values_list(*fields_, flat=flat)
        q._single = True  # type: ignore[attr-defined]
        return q  # type: ignore[return-value]

    def values(
        self, *args: str, **kwargs: str
    ) -> 'ValuesQuery[Literal[True]]':
        """Return values as dictionaries."""
        q = self.queryset.values(*args, **kwargs)
        q._single = True  # type: ignore[attr-defined]
        return q  # type: ignore[return-value]


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
        "_return_tuples",
        "_return_flat",
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
        self._return_tuples: bool = False
        self._return_flat: bool = False

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
            # Convert model instances to their primary key values
            if hasattr(value, 'pk'):
                value = value.pk
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
            db=self._db,
            q_objects=self._q_objects,
            update_data=kwargs
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
            q_objects=self._q_objects
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

    def as_tuples(self, flat: bool = False) -> 'QuerySet[MODEL]':
        """Return rows as tuples (no hydration). If flat=True, return first column only.

        Note: Best for simple selects without joins/annotations.
        """
        clone = self._clone()
        setattr(clone, '_return_tuples', True)
        setattr(clone, '_return_flat', bool(flat))
        return clone

    async def as_columns(self) -> dict[str, list[Any]]:
        """Execute and return columnar data as dict[column] -> list of values.

        Uses Rust engine execute_query_columns for fast dict-of-arrays.
        """
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")

        # Build SQL via IR
        base_table = self.model._meta.table_name
        if getattr(self, '_only_fields', None):
            select_fields = [f"{base_table}.{f}" for f in self._only_fields]
        else:
            select_fields = [f"{base_table}.{self.model._meta.fields_db_projection.get(fname, fname)}" for fname in self.model._meta.db_fields]

        # Minimal filters/ordering as in _execute
        and_conditions: dict[str, Any] = {}
        for q_obj in self._q_objects:
            if hasattr(q_obj, 'filters'):
                and_conditions.update(q_obj.filters)
            elif hasattr(q_obj, 'children'):
                for child in q_obj.children:
                    if hasattr(child, 'filters'):
                        and_conditions.update(child.filters)
                    elif isinstance(child, dict):
                        and_conditions.update(child)
            elif isinstance(q_obj, dict):
                and_conditions.update(q_obj)
        def _convert(cond: dict[str, Any]) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
            for key, value in cond.items():
                if '__' in key:
                    field_name, lookup = key.split('__', 1)
                    if lookup == 'startswith':
                        out.append({'field': field_name, 'op': 'like', 'value': f"{value}%"})
                    elif lookup == 'endswith':
                        out.append({'field': field_name, 'op': 'like', 'value': f"%{value}"})
                    elif lookup == 'contains':
                        out.append({'field': field_name, 'op': 'like', 'value': f"%{value}%"})
                    elif lookup in ('lt','lte','gt','gte','in','ne','not_in','nin','isnull','notnull'):
                        out.append({'field': field_name, 'op': lookup, 'value': value})
                    else:
                        out.append({'field': field_name, 'op': 'eq', 'value': value})
                else:
                    out.append({'field': key, 'op': 'eq', 'value': value})
            return out
        order_by = [ {'field': f, 'direction': d.value} for f, d in self._orderings ]
        conn_str = (getattr(db, 'connection_string', '') or getattr(db, '_connection_string', '')).lower()
        dialect = 'postgres' if 'postgresql' in conn_str else ('mysql' if 'mysql' in conn_str else 'sqlite')
        ir = {
            'dialect': dialect,
            'table': self.model._meta.table_name,
            'select': select_fields,
            'filters': _convert(and_conditions),
            'order_by': order_by,
            'limit': self._limit,
            'offset': self._offset,
        }
        if hasattr(db, '_rust_engine'):
            try:
                # Prefer compiled columns factory
                if hasattr(db._rust_engine, 'execute_compiled_ir_columns'):
                    data = await db._rust_engine.execute_ir_compiled_columns(ir)  # type: ignore[attr-defined]
                else:
                    data = await db._rust_engine.execute_ir_columns(ir)  # type: ignore[attr-defined]
                if isinstance(data, dict) and data:
                    return data
            except Exception:
                pass

        # Fallback: execute and pivot in Python
        try:
            from oxen_engine import build_sql_json
            import json as _json
            built = build_sql_json(_json.dumps(ir))
            query = built.get('sql')
            params = built.get('params')
        except Exception:
            query = f"SELECT {', '.join(select_fields)} FROM {self.model._meta.table_name}"
            params = []
        result = await db.execute_query(query, params if params else None)
        if result.get('error') is not None:
            raise OperationalError(f"Failed to execute columnar query: {result.get('error', 'Unknown error')}")
        rows = result.get('data', []) or []
        cols: dict[str, list[Any]] = {}
        for r in rows:
            if isinstance(r, dict):
                for k, v in r.items():
                    cols.setdefault(k, []).append(v)
        return cols

    async def as_arrow(self) -> Any:
        """Return results as a pyarrow.Table via Rust-backed column fetch.

        Requires env OXEN_ARROW=1 and `pyarrow` installed.
        """
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")
        # Build IR same as as_columns
        base_table = self.model._meta.table_name
        if getattr(self, '_only_fields', None):
            select_fields = [f"{base_table}.{f}" for f in self._only_fields]
        else:
            select_fields = [f"{base_table}.{self.model._meta.fields_db_projection.get(fname, fname)}" for fname in self.model._meta.db_fields]
        and_conditions: dict[str, Any] = {}
        for q_obj in self._q_objects:
            if hasattr(q_obj, 'filters'):
                and_conditions.update(q_obj.filters)
            elif hasattr(q_obj, 'children'):
                for child in q_obj.children:
                    if hasattr(child, 'filters'):
                        and_conditions.update(child.filters)
                    elif isinstance(child, dict):
                        and_conditions.update(child)
            elif isinstance(q_obj, dict):
                and_conditions.update(q_obj)
        def _convert(cond: dict[str, Any]) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
            for key, value in cond.items():
                if '__' in key:
                    field_name, lookup = key.split('__', 1)
                    if lookup == 'startswith':
                        out.append({'field': field_name, 'op': 'like', 'value': f"{value}%"})
                    elif lookup == 'endswith':
                        out.append({'field': field_name, 'op': 'like', 'value': f"%{value}"})
                    elif lookup == 'contains':
                        out.append({'field': field_name, 'op': 'like', 'value': f"%{value}%"})
                    elif lookup in ('lt','lte','gt','gte','in','ne','not_in','nin','isnull','notnull'):
                        out.append({'field': field_name, 'op': lookup, 'value': value})
                    else:
                        out.append({'field': field_name, 'op': 'eq', 'value': value})
                else:
                    out.append({'field': key, 'op': 'eq', 'value': value})
            return out
        order_by = [ {'field': f, 'direction': d.value} for f, d in self._orderings ]
        conn_str = (getattr(db, 'connection_string', '') or getattr(db, '_connection_string', '')).lower()
        dialect = 'postgres' if 'postgresql' in conn_str else ('mysql' if 'mysql' in conn_str else 'sqlite')
        ir = {
            'dialect': dialect,
            'table': self.model._meta.table_name,
            'select': select_fields,
            'filters': _convert(and_conditions),
            'order_by': order_by,
            'limit': self._limit,
            'offset': self._offset,
        }
        if hasattr(db, '_rust_engine'):
            try:
                # Use compiled columns and build arrow when native Arrow is unavailable
                try:
                    cols = await db._rust_engine.execute_ir_compiled_columns(ir)  # type: ignore[attr-defined]
                    import importlib, os as _os
                    _os.environ.setdefault('OXEN_ARROW', '1')
                    pa = importlib.import_module('pyarrow')
                    return pa.table(cols)
                except Exception:
                    return await db._rust_engine.execute_ir_arrow(ir)  # type: ignore[attr-defined]
            except Exception:
                pass
        # Fallback to Python arrow build
        try:
            import importlib, os as _os
            _os.environ.setdefault('OXEN_ARROW', '1')
            pa = importlib.import_module('pyarrow')
        except Exception:
            raise OperationalError("pyarrow is not installed. Install with: pip install pyarrow")
        columns = await self.as_columns()
        return pa.table(columns)

    async def as_numpy(self) -> Any:
        """Return results as dict[str, numpy.ndarray] using as_columns()."""
        try:
            import importlib
            np = importlib.import_module('numpy')
        except Exception:
            raise OperationalError("numpy is not installed. Install with: pip install numpy")
        cols = await self.as_columns()
        return {k: np.array(v) for k, v in cols.items()}

    async def iter(self, chunk_size: int = 1000) -> AsyncIterator[list[MODEL]]:
        """Async generator yielding results in chunks using paging (LIMIT/OFFSET)."""
        offset = 0
        while True:
            page = self._clone()
            page._limit = chunk_size
            page._offset = offset
            rows = await page
            if not rows:
                break
            yield rows
            offset += len(rows)

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

    def window(self, **kwargs: 'WindowFunction') -> 'QuerySet[MODEL]':
        """Add window functions to the query."""
        clone = self._clone()
        if not hasattr(clone, '_window_functions'):
            clone._window_functions = {}
        clone._window_functions.update(kwargs)
        return clone

    def with_cte(self, name: str, query: 'QuerySet', recursive: bool = False) -> 'QuerySet[MODEL]':
        """Add a Common Table Expression (CTE) to the query."""
        clone = self._clone()
        if not hasattr(clone, '_ctes'):
            clone._ctes = []
        clone._ctes.append({
            'name': name,
            'query': query,
            'recursive': recursive
        })
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
        
        # Build conditions from filters and collect OR groups
        and_conditions: dict[str, Any] = {}
        or_groups_source: list[list[dict[str, Any]]] = []
        for q_obj in self._q_objects:
            try:
                join_type = getattr(q_obj, 'join_type', 'AND')
            except Exception:
                join_type = 'AND'
            if join_type == 'OR' and (hasattr(q_obj, 'filters') or hasattr(q_obj, 'children')):
                group_filters: list[dict[str, Any]] = []
                if hasattr(q_obj, 'filters') and q_obj.filters:
                    group_filters.append(q_obj.filters)
                if hasattr(q_obj, 'children') and q_obj.children:
                    for child in q_obj.children:
                        if hasattr(child, 'filters') and child.filters:
                            group_filters.append(child.filters)
                        elif isinstance(child, dict) and child:
                            group_filters.append(child)
                if group_filters:
                    or_groups_source.append(group_filters)
            else:
                # Default AND accumulation
                if hasattr(q_obj, 'filters'):
                    and_conditions.update(q_obj.filters)
                elif hasattr(q_obj, 'children'):
                    for child in q_obj.children:
                        if hasattr(child, 'filters'):
                            and_conditions.update(child.filters)
                        elif isinstance(child, dict):
                            and_conditions.update(child)
                elif isinstance(q_obj, dict):
                    and_conditions.update(q_obj)
                else:
                    try:
                        and_conditions.update(dict(q_obj))
                    except Exception:
                        pass
        
        # Build the query
        # Default projection: only base table columns when not otherwise specified
        base_table = self.model._meta.table_name
        if getattr(self, '_only_fields', None):
            select_fields = [f"{base_table}.{f}" for f in self._only_fields]
        else:
            # project base table explicit columns instead of '*'
            select_fields = [f"{base_table}.{self.model._meta.fields_db_projection.get(fname, fname)}" for fname in self.model._meta.db_fields]
        
        # Add window functions to select fields
        if hasattr(self, '_window_functions') and self._window_functions:
            for alias, window_func in self._window_functions.items():
                if hasattr(window_func, 'to_sql'):
                    select_fields.append(f"{window_func.to_sql()} AS {alias}")
                else:
                    # Handle simple window functions
                    select_fields.append(f"{window_func} AS {alias}")
        
        # Build CTE part if CTEs exist (string without leading WITH)
        with_sql = ""
        if hasattr(self, '_ctes') and self._ctes:
            cte_clauses = []
            for cte in self._ctes:
                cte_name = cte['name']
                cte_query = cte['query']
                recursive = cte['recursive']
                
                # Get the SQL from the CTE query
                if hasattr(cte_query, 'sql'):
                    cte_sql = cte_query.sql()
                else:
                    # For now, use a simple approach
                    cte_sql = f"SELECT * FROM {cte_query.model._meta.table_name}"
                
                recursive_keyword = "RECURSIVE " if recursive else ""
                cte_clauses.append(f"{recursive_keyword}{cte_name} AS ({cte_sql})")
            with_sql = ", ".join(cte_clauses)
        
        # Build joins for select_related (inner joins) and project only joined PKs by default
        joins: list[dict[str, Any]] = []
        joined_projection: list[str] = []
        if self._select_related:
            try:
                for lookup in self._select_related:
                    current_model = self.model
                    current_table = self.model._meta.table_name
                    parts = lookup.split("__") if isinstance(lookup, str) else [str(lookup)]
                    for part in parts:
                        field_obj = current_model._meta.fields_map.get(part)
                        if field_obj is None:
                            break
                        # Expect relational fields
                        if not hasattr(field_obj, 'is_relational') or not field_obj.is_relational:
                            break
                        related_model = field_obj._get_related_model() if hasattr(field_obj, '_get_related_model') else None
                        if not related_model:
                            break
                        related_table = related_model._meta.table_name
                        left_col = f"{current_table}.{part}"
                        right_col = f"{related_table}.{related_model._meta.pk_attr}"
                        joins.append({
                            'join_type': 'inner',
                            'table': related_table,
                            'on': {
                                'left': left_col,
                                'op': '=',
                                'right': right_col,
                            }
                        })
                        # Project only the related PK by default to keep rows slim
                        joined_projection.append(f"{related_table}.{related_model._meta.pk_attr}")
                        current_model = related_model
                        current_table = related_table
            except Exception:
                # Best-effort: ignore join build errors
                joins = []
                joined_projection = []

        # Build IR for Rust builder
        conn_str = (getattr(db, 'connection_string', '') or getattr(db, '_connection_string', '')).lower()
        dialect = 'postgres' if 'postgresql' in conn_str else ('mysql' if 'mysql' in conn_str else 'sqlite')
        order_by = [
            {'field': field, 'direction': direction.value}
            for field, direction in self._orderings
        ]
        def _convert_condition_map(cond_map: dict[str, Any]) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
            for key, value in cond_map.items():
                if '__' in key:
                    field_name, lookup = key.split('__', 1)
                    if lookup == 'startswith':
                        out.append({'field': field_name, 'op': 'like', 'value': f"{value}%"})
                    elif lookup == 'istartswith':
                        out.append({'field': field_name, 'op': 'ilike', 'value': f"{value}%"})
                    elif lookup == 'endswith':
                        out.append({'field': field_name, 'op': 'like', 'value': f"%{value}"})
                    elif lookup == 'iendswith':
                        out.append({'field': field_name, 'op': 'ilike', 'value': f"%{value}"})
                    elif lookup == 'contains':
                        out.append({'field': field_name, 'op': 'like', 'value': f"%{value}%"})
                    elif lookup == 'icontains':
                        out.append({'field': field_name, 'op': 'ilike', 'value': f"%{value}%"})
                    elif lookup in ('lt','lte','gt','gte','in','ne','not_in','nin','isnull','notnull'):
                        out.append({'field': field_name, 'op': lookup, 'value': value})
                    else:
                        out.append({'field': field_name, 'op': 'eq', 'value': value})
                else:
                    out.append({'field': key, 'op': 'eq', 'value': value})
            return out

        filters = _convert_condition_map(and_conditions)
        groups: list[dict[str, Any]] = []
        for group in or_groups_source:
            group_filters: list[dict[str, Any]] = []
            for filt_map in group:
                group_filters.extend(_convert_condition_map(filt_map))
            if group_filters:
                groups.append({'kind': 'or', 'filters': group_filters})

        ir = {
            'dialect': dialect,
            'table': self.model._meta.table_name,
            'select': select_fields,
            'distinct': bool(getattr(self, '_distinct', False)),
            'filters': filters,
            'order_by': order_by,
            'limit': self._limit,
            'offset': self._offset,
        }
        if with_sql:
            ir['with_sql'] = with_sql
        if joins:
            ir['joins'] = joins
        if groups:
            ir['groups'] = groups
        if joined_projection:
            # Extend select list with joined PKs (or later extended columns)
            ir['select'] = select_fields + joined_projection

        # Execute via UnifiedEngine using single-hop Rust paths where possible
        # Fast path: if no joins/annotations/group-bys/window, request tuple rows, then hydrate
        use_tuple_mode = False
        try:
            no_joins = not joins
            no_annotations = not self._annotations
            no_group_bys = not self._group_bys
            no_windows = not getattr(self, '_window_functions', {})
            # If projection is simple base-table fields (either only() or default base projection)
            simple_projection = no_joins and no_annotations and no_group_bys and no_windows
            if simple_projection:
                use_tuple_mode = True
        except Exception:
            use_tuple_mode = False

        if use_tuple_mode and hasattr(db, '_rust_engine'):
            try:
                # Prefer IR-tuple execution to avoid double-compilation
                tuple_rows = await db._rust_engine.execute_ir_tuples(ir)  # type: ignore[attr-defined]
                # Map select columns back to model field names
                select_cols = ir.get('select') or []
                # Reverse projection map: db_column -> model_field
                rev_proj = {v: k for k, v in self.model._meta.fields_db_projection.items()}
                col_names: list[str] = []
                for c in select_cols:
                    # c may be "table.col" or an expression like "... AS alias"; handle basic table.col
                    name = c.split('.')[-1].strip().split(' AS ')[0].strip('"')
                    model_field = rev_proj.get(name, name)
                    if model_field in self.model._meta.fields_map:
                        col_names.append(model_field)
                if not col_names:
                    col_names = list(self.model._meta.db_fields)
                instances: list[MODEL] = []
                for r in tuple_rows:
                    data = {col_names[i]: r[i] for i in range(min(len(col_names), len(r)))}
                    instance = self.model._init_from_db(**data)
                    instance._meta.db = db
                    instances.append(instance)
                return instances
            except Exception:
                pass

        # Global tuple-return opt-in for plain reads (skip hydration)
        if getattr(self, '_return_tuples', False) and not joins and hasattr(db, '_rust_engine'):
            try:
                tuple_rows = await db._rust_engine.execute_query_tuples(query, params if params else None)  # type: ignore[attr-defined]
                if getattr(self, '_return_flat', False):
                    return [r[0] if r else None for r in tuple_rows]
                return [tuple(r) for r in tuple_rows]
            except Exception:
                pass

        # Prefer zero-copy-ish dict rows from Rust when available (single IR hop)
        if hasattr(db, '_rust_engine'):
            try:
                # Prefer Rust-side model hydration when projection maps cleanly
                select_cols = ir.get('select') or []
                rev_proj = {v: k for k, v in self.model._meta.fields_db_projection.items()}
                indices: list[int] = []
                names: list[str] = []
                for idx, c in enumerate(select_cols):
                    name = c.split('.')[-1].strip().split(' AS ')[0].strip('"')
                    model_field = rev_proj.get(name, name)
                    if model_field in self.model._meta.fields_map:
                        indices.append(idx)
                        names.append(model_field)
                if indices and names and len(indices) == len(select_cols):
                    return await db._rust_engine.execute_ir_models(ir, self.model, getattr(db, '_rust_engine', db), indices, names)  # type: ignore[attr-defined]

                # Fallback: Let Rust build SQL and return dict rows
                res = await db._rust_engine.execute_ir(ir)  # type: ignore[attr-defined]
                rows = res.get('data', []) if isinstance(res, dict) else []
                instances: list[MODEL] = []
                if rows and joins:
                    seen: dict[Any, Any] = {}
                    pk_attr = self.model._meta.pk_attr
                    for record in rows:
                        pk_val = record.get(pk_attr)
                        if pk_val in seen:
                            continue
                        instance = self.model._init_from_db(**record)
                        instance._meta.db = db
                        instances.append(instance)
                        seen[pk_val] = instance
                else:
                    for record in rows:
                        instance = self.model._init_from_db(**record)
                        instance._meta.db = db
                        instances.append(instance)
                return instances
            except Exception:
                pass

        # Fallback: build SQL and execute via engine
        try:
            from oxen_engine import build_sql_json
            import json as _json
            built = build_sql_json(_json.dumps(ir))
            query = built.get('sql')
            params = built.get('params')
        except Exception:
            query = f"SELECT * FROM {self.model._meta.table_name}"
            params = []
        result = await db.execute_query(query, params if params else None)
        if result.get('error') is not None:
            raise OperationalError(f"Failed to execute query: {result.get('error', 'Unknown error')}")
        records = result.get('data', [])
        instances = []
        for record in records:
            instance = self.model._init_from_db(**record)
            instance._meta.db = db
            instances.append(instance)
        return instances


# Placeholder classes for other query types
class UpdateQuery(AwaitableQuery):
    """Query for updating records."""
    
    def __init__(self, model: type[MODEL], db: Any = None, q_objects: list[Q] = None, update_data: dict[str, Any] = None):
        super().__init__(model)
        self._db = db
        self._q_objects = q_objects or []
        self._update_data = update_data or {}
    
    def __await__(self) -> Generator[Any, None, int]:
        """Make the update query awaitable."""
        async def _self() -> int:
            return await self._execute()
        return _self().__await__()
    
    async def _execute(self) -> int:
        """Execute the update query and return number of rows affected.

        Optimizations:
        - If updating a single field across multiple ids, generate one UPDATE ... WHERE id IN (...)
        - If updating multiple fields with per-id values, use CASE ... WHEN id THEN value END
        """
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")

        # Gather conditions
        conditions = {}
        for q_obj in self._q_objects:
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
                try:
                    conditions.update(dict(q_obj))
                except:
                    pass

        conn_str = (getattr(db, 'connection_string', '') or getattr(db, '_connection_string', '')).lower()
        dialect = 'postgres' if 'postgresql' in conn_str else ('mysql' if 'mysql' in conn_str else 'sqlite')
        # Convert filters
        filters = []
        for key, value in conditions.items():
            if '__' in key:
                field_name, lookup = key.split('__', 1)
                if lookup == 'startswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"{value}%"})
                elif lookup == 'endswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}"})
                elif lookup == 'contains':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}%"})
                elif lookup in ('lt','lte','gt','gte','in','ne'):
                    filters.append({'field': field_name, 'op': lookup, 'value': value})
                else:
                    filters.append({'field': field_name, 'op': 'eq', 'value': value})
            else:
                filters.append({'field': key, 'op': 'eq', 'value': value})
        # Build IR
        # Attempt optimized SQL generation for common patterns
        id_list = None
        if any(f.get('field') == 'id' and f.get('op') in ('in', 'eq') for f in filters):
            # Extract id list for IN filter
            for f in filters:
                if f.get('field') == 'id' and f.get('op') == 'in':
                    id_list = f.get('value', [])
                if f.get('field') == 'id' and f.get('op') == 'eq':
                    id_list = [f.get('value')]

        query = None
        params = None
        if id_list and isinstance(id_list, list) and self._update_data:
            # Single-field same value across ids
            if len(self._update_data) == 1:
                field, value = next(iter(self._update_data.items()))
                placeholders = ', '.join(['?' for _ in id_list])
                query = f'UPDATE "{self.model._meta.table_name}" SET "{field}" = ? WHERE "id" IN ({placeholders})'
                params = [value] + id_list
            else:
                # CASE-based update is complex; fallback to IR builder
                query = None
        if query is None:
            ir = {
                'dialect': dialect,
                'table': self.model._meta.table_name,
                'action': 'update',
                'set': self._update_data,
                'filters': filters,
            }
            try:
                from oxen_engine import build_sql_json
                import json as _json
                built = build_sql_json(_json.dumps(ir))
                query = built.get('sql')
                params = built.get('params')
            except Exception:
                raise OperationalError("Rust IR builder unavailable for update")

        result = await db.execute_query(query, params if params else None)
        if result.get('error') is None:
            return result.get('rows_affected', 0)
        else:
            raise OperationalError(f"Failed to execute update query: {result.get('error', 'Unknown error')}")

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
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")

        # Gather conditions
        conditions = {}
        for q_obj in self._q_objects:
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
                try:
                    conditions.update(dict(q_obj))
                except:
                    pass

        conn_str = (getattr(db, 'connection_string', '') or getattr(db, '_connection_string', '')).lower()
        dialect = 'postgres' if 'postgresql' in conn_str else ('mysql' if 'mysql' in conn_str else 'sqlite')
        filters = []
        for key, value in conditions.items():
            if '__' in key:
                field_name, lookup = key.split('__', 1)
                if lookup == 'startswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"{value}%"})
                elif lookup == 'endswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}"})
                elif lookup == 'contains':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}%"})
                elif lookup in ('lt','lte','gt','gte','in','ne'):
                    filters.append({'field': field_name, 'op': lookup, 'value': value})
                else:
                    filters.append({'field': field_name, 'op': 'eq', 'value': value})
            else:
                filters.append({'field': key, 'op': 'eq', 'value': value})

        ir = {
            'dialect': dialect,
            'table': self.model._meta.table_name,
            'action': 'delete',
            'filters': filters,
        }
        try:
            from oxen_engine import build_sql_json
            import json as _json
            built = build_sql_json(_json.dumps(ir))
            query = built.get('sql')
            params = built.get('params')
        except Exception:
            raise OperationalError("Rust IR builder unavailable for delete")

        result = await db.execute_query(query, params if params else None)
        if result.get('error') is None:
            return result.get('rows_affected', 0)
        else:
            raise OperationalError(f"Failed to execute delete query: {result.get('error', 'Unknown error')}")

class ExistsQuery(AwaitableQuery):
    """Query for checking existence."""
    
    def __init__(self, model: type[MODEL], db: Any = None, q_objects: list[Q] = None):
        super().__init__(model)
        self._db = db
        self._q_objects = q_objects or []
    
    def __await__(self) -> Generator[Any, None, bool]:
        """Make the exists query awaitable."""
        async def _self() -> bool:
            return await self._execute()
        return _self().__await__()
    
    async def _execute(self) -> bool:
        """Execute the exists query using IR: SELECT 1 ... LIMIT 1."""
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")

        # Build conditions
        conditions: dict[str, Any] = {}
        for q_obj in self._q_objects:
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
                try:
                    conditions.update(dict(q_obj))
                except:
                    pass

        conn_str = (getattr(db, 'connection_string', '') or getattr(db, '_connection_string', '')).lower()
        dialect = 'postgres' if 'postgresql' in conn_str else ('mysql' if 'mysql' in conn_str else 'sqlite')
        filters: list[dict[str, Any]] = []
        for key, value in conditions.items():
            if '__' in key:
                field_name, lookup = key.split('__', 1)
                if lookup == 'startswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"{value}%"})
                elif lookup == 'endswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}"})
                elif lookup == 'contains':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}%"})
                elif lookup in ('lt','lte','gt','gte','in','ne'):
                    filters.append({'field': field_name, 'op': lookup, 'value': value})
                else:
                    filters.append({'field': field_name, 'op': 'eq', 'value': value})
            else:
                filters.append({'field': key, 'op': 'eq', 'value': value})

        ir = {
            'dialect': dialect,
            'table': self.model._meta.table_name,
            'select': ['1'],
            'filters': filters,
            'limit': 1,
        }
        try:
            from oxen_engine import build_sql_json
            import json as _json
            built = build_sql_json(_json.dumps(ir))
            query = built.get('sql')
            params = built.get('params')
        except Exception:
            query = f"SELECT 1 FROM {self.model._meta.table_name} LIMIT 1"
            params = []

        result = await db.execute_query(query, params if params else None)
        if result.get('error') is None:
            data = result.get('data', [])
            return bool(data)
        else:
            raise OperationalError(f"Failed to execute exists query: {result.get('error', 'Unknown error')}")

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
        
        # Build IR for COUNT(*) with filters
        conn_str = (getattr(db, 'connection_string', '') or getattr(db, '_connection_string', '')).lower()
        dialect = 'postgres' if 'postgresql' in conn_str else ('mysql' if 'mysql' in conn_str else 'sqlite')
        filters = []
        for key, value in conditions.items():
            if '__' in key:
                field_name, lookup = key.split('__', 1)
                if lookup == 'startswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"{value}%"})
                elif lookup == 'endswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}"})
                elif lookup == 'contains':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}%"})
                elif lookup in ('lt','lte','gt','gte','in','ne'):
                    filters.append({'field': field_name, 'op': lookup, 'value': value})
                else:
                    filters.append({'field': field_name, 'op': 'eq', 'value': value})
            else:
                filters.append({'field': key, 'op': 'eq', 'value': value})
        ir = {
            'dialect': dialect,
            'table': self.model._meta.table_name,
            'select': ['COUNT(*) as count'],
            'filters': filters,
        }
        try:
            from oxen_engine import build_sql_json
            import json as _json
            built = build_sql_json(_json.dumps(ir))
            query = built.get('sql')
            params = built.get('params')
        except Exception:
            query = f"SELECT COUNT(*) as count FROM {self.model._meta.table_name}"
            params = []
        
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
    def __init__(
        self,
        model: type[MODEL],
        db: Any = None,
        q_objects: list[Q] | None = None,
        single: bool = False,
        raise_does_not_exist: bool = False,
        fields_for_select_list: tuple[str, ...] = (),
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        distinct: bool = False,
        orderings: list[tuple[str, Order]] | None = None,
        flat: bool = False,
        annotations: dict[str, Any] | None = None,
        custom_filters: dict[str, Any] | None = None,
        group_bys: tuple[str, ...] | None = None,
        force_indexes: set[str] | None = None,
        use_indexes: set[str] | None = None,
    ) -> None:
        super().__init__(model)
        self._db = db
        self._q_objects = q_objects or []
        self._single = single
        self._raise_does_not_exist = raise_does_not_exist
        self._fields = fields_for_select_list
        self._limit = limit
        self._offset = offset
        self._distinct = distinct
        self._orderings = orderings or []
        self._flat = flat
        self._annotations = annotations or {}
        self._custom_filters = custom_filters or {}
        self._group_bys = group_bys or ()
        self._force_indexes = force_indexes or set()
        self._use_indexes = use_indexes or set()

    def __await__(self) -> Generator[Any, None, Any]:
        async def _self() -> Any:
            return await self._execute()
        return _self().__await__()

    async def _execute(self) -> Any:
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")

        # Build conditions
        conditions: dict[str, Any] = {}
        for q_obj in self._q_objects:
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
                try:
                    conditions.update(dict(q_obj))
                except Exception:
                    pass

        # Select fields
        fields = list(self._fields) if self._fields else [self.model._meta.pk_attr]
        # When flat=True, expect exactly one field
        if self._flat and len(fields) != 1:
            raise ValueError("flat=True requires exactly one selected field")

        # Determine dialect
        conn_str = (getattr(db, 'connection_string', '') or getattr(db, '_connection_string', '')).lower()
        dialect = 'postgres' if 'postgresql' in conn_str else ('mysql' if 'mysql' in conn_str else 'sqlite')

        # Build filters IR
        filters: list[dict[str, Any]] = []
        for key, value in conditions.items():
            if '__' in key:
                field_name, lookup = key.split('__', 1)
                if lookup == 'startswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"{value}%"})
                elif lookup == 'istartswith':
                    filters.append({'field': field_name, 'op': 'ilike', 'value': f"{value}%"})
                elif lookup == 'endswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}"})
                elif lookup == 'iendswith':
                    filters.append({'field': field_name, 'op': 'ilike', 'value': f"%{value}"})
                elif lookup == 'contains':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}%"})
                elif lookup == 'icontains':
                    filters.append({'field': field_name, 'op': 'ilike', 'value': f"%{value}%"})
                elif lookup in ('lt','lte','gt','gte','in','ne','not_in','nin','isnull','notnull'):
                    filters.append({'field': field_name, 'op': lookup, 'value': value})
                else:
                    filters.append({'field': field_name, 'op': 'eq', 'value': value})
            else:
                filters.append({'field': key, 'op': 'eq', 'value': value})

        order_by = [
            {'field': field, 'direction': direction.value}
            for field, direction in self._orderings
        ]

        ir = {
            'dialect': dialect,
            'table': self.model._meta.table_name,
            'select': fields,
            'distinct': bool(self._distinct),
            'filters': filters,
            'order_by': order_by,
            'limit': self._limit or (1 if self._single else None),
            'offset': self._offset,
        }

        # Single-hop IR tuple path when available
        if hasattr(db, '_rust_engine'):
            try:
                tuple_rows = await db._rust_engine.execute_ir_tuples(ir)  # type: ignore[attr-defined]
                values = [list(r) for r in tuple_rows]
                if self._flat:
                    values = [v[0] if v else None for v in values]
                if self._single:
                    if not values:
                        if getattr(self, '_raise_does_not_exist', False):
                            raise DoesNotExist(f"No {self.model.__name__} matches the given query.")
                        return None if self._flat else []
                    return values[0]
                return values
            except Exception:
                pass

        # Prefer zero-copy-ish dict rows (though values_list expects tuples, we pivot if dicts)
        rows = None
        if hasattr(db, '_rust_engine'):
            try:
                res = await db._rust_engine.execute_ir(ir)  # type: ignore[attr-defined]
                rows = res.get('data', []) if isinstance(res, dict) else None
            except Exception:
                rows = None
        if rows is None:
            try:
                from oxen_engine import build_sql_json
                import json as _json
                built = build_sql_json(_json.dumps(ir))
                query = built.get('sql')
                params = built.get('params')
            except Exception:
                quoted_table = f'"{self.model._meta.table_name}"'
                select_cols = ', '.join([f'"{c}"' for c in fields])
                query = f"SELECT {select_cols} FROM {quoted_table}"
                params = []
            result = await db.execute_query(query, params if params else None)
            if result.get('error') is not None:
                raise OperationalError(f"Failed to execute values_list query: {result.get('error', 'Unknown error')}")
            rows = result.get('data', []) or []

        # Normalize rows: engine typically returns list[dict]
        def row_to_list(r: Any) -> list[Any]:
            if isinstance(r, dict):
                return [r.get(col) for col in fields]
            if isinstance(r, (list, tuple)):
                return list(r)
            return [r]

        values = [row_to_list(r) for r in rows]
        if self._flat:
            values = [v[0] if v else None for v in values]
        if self._single:
            if not values:
                if getattr(self, '_raise_does_not_exist', False):
                    raise DoesNotExist(f"No {self.model.__name__} matches the given query.")
                return None if self._flat else []
            return values[0]
        return values

class ValuesQuery(AwaitableQuery, Generic[SINGLE]):
    """Query for returning values as dictionaries."""
    def __init__(
        self,
        model: type[MODEL],
        db: Any = None,
        q_objects: list[Q] | None = None,
        single: bool = False,
        raise_does_not_exist: bool = False,
        fields_for_select: dict[str, str] | None = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        distinct: bool = False,
        orderings: list[tuple[str, Order]] | None = None,
        annotations: dict[str, Any] | None = None,
        custom_filters: dict[str, Any] | None = None,
        group_bys: tuple[str, ...] | None = None,
        force_indexes: set[str] | None = None,
        use_indexes: set[str] | None = None,
    ) -> None:
        super().__init__(model)
        self._db = db
        self._q_objects = q_objects or []
        self._single = single
        self._raise_does_not_exist = raise_does_not_exist
        self._fields_map = fields_for_select or {}
        self._limit = limit
        self._offset = offset
        self._distinct = distinct
        self._orderings = orderings or []
        self._annotations = annotations or {}
        self._custom_filters = custom_filters or {}
        self._group_bys = group_bys or ()
        self._force_indexes = force_indexes or set()
        self._use_indexes = use_indexes or set()

    def __await__(self) -> Generator[Any, None, Any]:
        async def _self() -> Any:
            return await self._execute()
        return _self().__await__()

    async def _execute(self) -> Any:
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")

        # Build conditions
        conditions: dict[str, Any] = {}
        for q_obj in self._q_objects:
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
                try:
                    conditions.update(dict(q_obj))
                except Exception:
                    pass

        # Determine select list with aliases
        if self._fields_map:
            fields = []
            aliases = []
            for alias, field_name in self._fields_map.items():
                # Use raw "field AS alias" so builder preserves alias
                fields.append(f"{field_name} AS {alias}")
                aliases.append(alias)
        else:
            # Default to all columns
            fields = ["*"]
            aliases = []

        # Determine dialect
        conn_str = (getattr(db, 'connection_string', '') or getattr(db, '_connection_string', '')).lower()
        dialect = 'postgres' if 'postgresql' in conn_str else ('mysql' if 'mysql' in conn_str else 'sqlite')

        # Build filters IR
        filters: list[dict[str, Any]] = []
        for key, value in conditions.items():
            if '__' in key:
                field_name, lookup = key.split('__', 1)
                if lookup == 'startswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"{value}%"})
                elif lookup == 'istartswith':
                    filters.append({'field': field_name, 'op': 'ilike', 'value': f"{value}%"})
                elif lookup == 'endswith':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}"})
                elif lookup == 'iendswith':
                    filters.append({'field': field_name, 'op': 'ilike', 'value': f"%{value}"})
                elif lookup == 'contains':
                    filters.append({'field': field_name, 'op': 'like', 'value': f"%{value}%"})
                elif lookup == 'icontains':
                    filters.append({'field': field_name, 'op': 'ilike', 'value': f"%{value}%"})
                elif lookup in ('lt','lte','gt','gte','in','ne','not_in','nin','isnull','notnull'):
                    filters.append({'field': field_name, 'op': lookup, 'value': value})
                else:
                    filters.append({'field': field_name, 'op': 'eq', 'value': value})
            else:
                filters.append({'field': key, 'op': 'eq', 'value': value})

        order_by = [
            {'field': field, 'direction': direction.value}
            for field, direction in self._orderings
        ]

        ir = {
            'dialect': dialect,
            'table': self.model._meta.table_name,
            'select': fields,
            'distinct': bool(self._distinct),
            'filters': filters,
            'order_by': order_by,
            'limit': self._limit or (1 if self._single else None),
            'offset': self._offset,
        }

        # Prefer compiled columns fast path: fetch dict[column]->list once, then build row dicts in Python
        if hasattr(db, '_rust_engine'):
            try:
                cols = None
                if hasattr(db._rust_engine, 'execute_ir_compiled_columns'):
                    cols = await db._rust_engine.execute_ir_compiled_columns(ir)  # type: ignore[attr-defined]
                elif hasattr(db._rust_engine, 'execute_ir_columns'):
                    cols = await db._rust_engine.execute_ir_columns(ir)  # type: ignore[attr-defined]
                if isinstance(cols, dict) and cols:
                    # Determine the output column order (aliases if provided)
                    out_cols = list(self._fields_map.keys()) if self._fields_map else list(cols.keys())
                    # Build list[dict] row-wise from columns
                    row_count = len(next(iter(cols.values()))) if cols else 0
                    data: list[dict[str, Any]] = []
                    for i in range(row_count):
                        row: dict[str, Any] = {}
                        for c in out_cols:
                            # When aliases used, column keys are aliases
                            row[c] = cols.get(c, [None] * row_count)[i]
                        data.append(row)
                    if self._single:
                        if not data:
                            if getattr(self, '_raise_does_not_exist', False):
                                raise DoesNotExist(f"No {self.model.__name__} matches the given query.")
                            return None
                        return data[0]
                    return data
            except Exception:
                pass

        # Prefer single-hop IR execution
        if hasattr(db, '_rust_engine'):
            try:
                res = await db._rust_engine.execute_ir(ir)  # type: ignore[attr-defined]
                rows = res.get('data', []) if isinstance(res, dict) else []
            except Exception:
                rows = None
        else:
            rows = None
        if rows is None:
            try:
                from oxen_engine import build_sql_json
                import json as _json
                built = build_sql_json(_json.dumps(ir))
                query = built.get('sql')
                params = built.get('params')
            except Exception:
                quoted_table = f'"{self.model._meta.table_name}"'
                select_cols = ', '.join([f'"{c}"' for c in (aliases or [])]) if aliases else '*'
                query = f"SELECT {select_cols} FROM {quoted_table}"
                params = []
            result = await db.execute_query(query, params if params else None)
            if result.get('error') is not None:
                raise OperationalError(f"Failed to execute values query: {result.get('error', 'Unknown error')}")
            rows = result.get('data', []) or []

        # If aliases were used, ensure dict keys align
        def to_dict(r: Any) -> dict[str, Any]:
            if isinstance(r, dict):
                return r
            if isinstance(r, (list, tuple)) and aliases:
                return {alias: r[i] for i, alias in enumerate(aliases)}
            return {'value': r}

        data = [to_dict(r) for r in rows]
        if self._single:
            if not data:
                if getattr(self, '_raise_does_not_exist', False):
                    raise DoesNotExist(f"No {self.model.__name__} matches the given query.")
                return None
            return data[0]
        return data

class RawSQLQuery(AwaitableQuery):
    """Query for executing raw SQL."""
    def __init__(self, model: type[MODEL], db: Any = None, sql: str = "") -> None:
        super().__init__(model)
        self._db = db
        self._sql = sql

    def __await__(self) -> Generator[Any, None, list[dict[str, Any]]]:
        async def _self() -> list[dict[str, Any]]:
            return await self._execute()
        return _self().__await__()

    async def _execute(self) -> list[dict[str, Any]]:
        db = self._choose_db()
        if not db:
            raise OperationalError("No database connection available")
        result = await db.execute_query(self._sql)
        if result.get('error') is not None:
            raise OperationalError(f"Failed to execute raw SQL: {result.get('error', 'Unknown error')}")
        return result.get('data', []) or []

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