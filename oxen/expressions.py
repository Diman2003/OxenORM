#!/usr/bin/env python3
"""
OxenORM Expressions System

This module provides the expressions functionality for OxenORM,
inspired by Tortoise ORM but optimized for OxenORM's architecture.
"""

import operator
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import Enum
from typing import TYPE_CHECKING, Any, cast, Union, Optional, List, Dict

from oxen.exceptions import FieldError, OperationalError, ValidationError
from oxen.fields.base import Field
from oxen.fields.data import JSONField
from oxen.fields.relational import RelationalField
from oxen.filters import FilterInfoDict
from oxen.query_utils import (
    QueryModifier,
    TableCriterionTuple,
    get_joins_for_related_field,
    resolve_field_json_path,
    resolve_nested_field,
)

if TYPE_CHECKING:  # pragma: nocoverage
    from oxen.models import Model
    from oxen.queryset import AwaitableQuery


@dataclass(frozen=True)
class ResolveContext:
    """Context for resolving expressions."""
    model: type['Model']
    table: str
    annotations: dict[str, Any]
    custom_filters: dict[str, FilterInfoDict]


@dataclass
class ResolveResult:
    """Result of expression resolution."""
    term: str
    joins: list[TableCriterionTuple] = dataclass_field(default_factory=list)
    output_field: Field | None = None


class Expression:
    """
    Parent class for expressions.
    """

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        """Resolve the expression to SQL."""
        raise NotImplementedError()


class Value(Expression):
    """
    Wrapper for a value that should be used as a term in a query.
    """

    def __init__(self, value: Any) -> None:
        self.value = value

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        return ResolveResult(term=str(self.value))


class Connector(Enum):
    """Arithmetic connectors."""
    add = "add"
    sub = "sub"
    mul = "mul"
    div = "truediv"
    pow = "pow"
    mod = "mod"


class CombinedExpression(Expression):
    """Combined arithmetic expression."""
    
    def __init__(self, left: Expression, connector: Connector, right: Any) -> None:
        self.left = left
        self.connector = connector
        self.right = right if isinstance(right, Expression) else Value(right)

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        left = self.left.resolve(resolve_context)
        right = self.right.resolve(resolve_context)
        
        # Build SQL expression
        if self.connector == Connector.add:
            term = f"({left.term} + {right.term})"
        elif self.connector == Connector.sub:
            term = f"({left.term} - {right.term})"
        elif self.connector == Connector.mul:
            term = f"({left.term} * {right.term})"
        elif self.connector == Connector.div:
            term = f"({left.term} / {right.term})"
        elif self.connector == Connector.pow:
            term = f"POWER({left.term}, {right.term})"
        elif self.connector == Connector.mod:
            term = f"({left.term} % {right.term})"
        else:
            term = f"({left.term} {self.connector.value} {right.term})"
        
        return ResolveResult(term=term)


class F(Expression):
    """
    F() expressions allow you to reference model field values and perform
    database operations using them without having to pull them into Python memory.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        """Resolve F expression to field reference."""
        model = resolve_context.model
        table = resolve_context.table
        
        # Handle nested field lookups (e.g., "user__name")
        if "__" in self.name:
            field_parts = self.name.split("__")
            current_model = model
            current_table = table
            joins = []
            
            for i, field_part in enumerate(field_parts[:-1]):
                if field_part not in current_model._meta.fields_map:
                    raise FieldError(f"Field '{field_part}' not found in model {current_model.__name__}")
                
                field_obj = current_model._meta.fields_map[field_part]
                if not isinstance(field_obj, RelationalField):
                    raise FieldError(f"Field '{field_part}' is not a relational field")
                
                # Get related model and table
                related_model = field_obj.related_model
                related_table = related_model._meta.table_name
                
                # Create join
                join = (related_table, f"{current_table}.{field_part}_id = {related_table}.id")
                joins.append(join)
                
                current_model = related_model
                current_table = related_table
            
            # Final field
            final_field = field_parts[-1]
            if final_field not in current_model._meta.fields_map:
                raise FieldError(f"Field '{final_field}' not found in model {current_model.__name__}")
            
            term = f"{current_table}.{final_field}"
            return ResolveResult(term=term, joins=joins)
        else:
            # Simple field reference
            if self.name not in model._meta.fields_map:
                raise FieldError(f"Field '{self.name}' not found in model {model.__name__}")
            
            term = f"{table}.{self.name}"
            return ResolveResult(term=term)

    def _combine(self, other: Any, connector: Connector, right_hand: bool) -> CombinedExpression:
        """Combine with another expression."""
        if right_hand:
            return CombinedExpression(Value(other), connector, self)
        else:
            return CombinedExpression(self, connector, other)

    def __neg__(self) -> CombinedExpression:
        """Negate the expression."""
        return CombinedExpression(Value(0), Connector.sub, self)

    def __add__(self, other) -> CombinedExpression:
        """Add to another expression."""
        return self._combine(other, Connector.add, False)

    def __sub__(self, other) -> CombinedExpression:
        """Subtract from another expression."""
        return self._combine(other, Connector.sub, False)

    def __mul__(self, other) -> CombinedExpression:
        """Multiply by another expression."""
        return self._combine(other, Connector.mul, False)

    def __truediv__(self, other) -> CombinedExpression:
        """Divide by another expression."""
        return self._combine(other, Connector.div, False)

    def __mod__(self, other) -> CombinedExpression:
        """Modulo with another expression."""
        return self._combine(other, Connector.mod, False)

    def __pow__(self, other) -> CombinedExpression:
        """Power of another expression."""
        return self._combine(other, Connector.pow, False)

    def __radd__(self, other) -> CombinedExpression:
        """Right add."""
        return self._combine(other, Connector.add, True)

    def __rsub__(self, other) -> CombinedExpression:
        """Right subtract."""
        return self._combine(other, Connector.sub, True)

    def __rmul__(self, other) -> CombinedExpression:
        """Right multiply."""
        return self._combine(other, Connector.mul, True)

    def __rtruediv__(self, other) -> CombinedExpression:
        """Right divide."""
        return self._combine(other, Connector.div, True)

    def __rmod__(self, other) -> CombinedExpression:
        """Right modulo."""
        return self._combine(other, Connector.mod, True)

    def __rpow__(self, other) -> CombinedExpression:
        """Right power."""
        return self._combine(other, Connector.pow, True)


class Subquery:
    """Subquery expression."""
    
    def __init__(self, query: 'AwaitableQuery') -> None:
        self.query = query

    def get_sql(self) -> str:
        """Get SQL for the subquery."""
        return f"({self.query.sql()})"

    def as_(self, alias: str) -> str:
        """Alias the subquery."""
        return f"({self.query.sql()}) AS {alias}"


class RawSQL:
    """Raw SQL expression."""
    
    def __init__(self, sql: str) -> None:
        self.sql = sql

    def get_sql(self) -> str:
        """Get the raw SQL."""
        return self.sql


class Q:
    """
    Q Expression container.
    Q Expressions are a useful tool to compose a query from many small parts.
    """

    __slots__ = (
        "children",
        "filters",
        "join_type",
        "_is_negated",
    )

    AND = "AND"
    OR = "OR"

    def __init__(self, *args: 'Q', join_type: str = AND, **kwargs: Any) -> None:
        """
        Initialize Q expression.
        
        Args:
            *args: Inner Q expressions
            join_type: Join type (AND or OR)
            **kwargs: Filter statements
        """
        self.children = list(args)
        self.filters = kwargs
        self.join_type = join_type
        self._is_negated = False

    def __and__(self, other: 'Q') -> 'Q':
        """Combine with AND."""
        if self.join_type == self.AND:
            new_q = Q(*self.children, join_type=self.AND, **self.filters)
            new_q.children.append(other)
            return new_q
        else:
            return Q(self, other, join_type=self.AND)

    def __or__(self, other: 'Q') -> 'Q':
        """Combine with OR."""
        if self.join_type == self.OR:
            new_q = Q(*self.children, join_type=self.OR, **self.filters)
            new_q.children.append(other)
            return new_q
        else:
            return Q(self, other, join_type=self.OR)

    def __invert__(self) -> 'Q':
        """Negate the expression."""
        new_q = Q(*self.children, join_type=self.join_type, **self.filters)
        new_q._is_negated = True
        return new_q

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Q):
            return False
        return (
            self.children == other.children
            and self.filters == other.filters
            and self.join_type == other.join_type
            and self._is_negated == other._is_negated
        )

    def negate(self) -> None:
        """Negate this expression in place."""
        self._is_negated = not self._is_negated

    def _resolve_nested_filter(
        self, resolve_context: ResolveContext, key: str, value: Any, table: str
    ) -> QueryModifier:
        """Resolve nested filter (e.g., field__lookup)."""
        if "__" not in key:
            return QueryModifier()
        
        field_name, lookup = key.split("__", 1)
        
        # Handle JSON field lookups
        if lookup.startswith("json_"):
            return self._resolve_json_filter(resolve_context, field_name, lookup, value, table)
        
        # Handle relational field lookups
        if field_name in resolve_context.model._meta.fields_map:
            field_obj = resolve_context.model._meta.fields_map[field_name]
            if isinstance(field_obj, RelationalField):
                return self._resolve_relational_filter(resolve_context, field_name, lookup, value, table)
        
        # Handle regular field lookups
        return self._resolve_regular_filter(resolve_context, key, value, table)

    def _resolve_json_filter(
        self, resolve_context: ResolveContext, field_name: str, lookup: str, value: Any, table: str
    ) -> QueryModifier:
        """Resolve JSON field filter."""
        # This would be implemented with actual JSON filtering logic
        return QueryModifier()

    def _resolve_relational_filter(
        self, resolve_context: ResolveContext, field_name: str, lookup: str, value: Any, table: str
    ) -> QueryModifier:
        """Resolve relational field filter."""
        # This would be implemented with actual relational filtering logic
        return QueryModifier()

    def _resolve_regular_filter(
        self, resolve_context: ResolveContext, key: str, value: Any, table: str
    ) -> QueryModifier:
        """Resolve regular field filter."""
        # This would be implemented with actual field filtering logic
        return QueryModifier()

    def _resolve_custom_kwarg(
        self, resolve_context: ResolveContext, key: str, value: Any, table: str
    ) -> QueryModifier:
        """Resolve custom keyword argument."""
        # This would be implemented with actual custom filter logic
        return QueryModifier()

    def _process_filter_kwarg(
        self, model: type['Model'], key: str, value: Any, table: str
    ) -> tuple[str, Any]:
        """Process filter keyword argument."""
        # This would be implemented with actual filter processing logic
        return key, value

    def _resolve_regular_kwarg(
        self, resolve_context: ResolveContext, key: str, value: Any, table: str
    ) -> QueryModifier:
        """Resolve regular keyword argument."""
        # This would be implemented with actual keyword resolution logic
        return QueryModifier()

    def _get_actual_filter_params(
        self, resolve_context: ResolveContext, key: str, value: Any
    ) -> tuple[str, Any]:
        """Get actual filter parameters."""
        # This would be implemented with actual parameter extraction logic
        return key, value

    def _resolve_kwargs(self, resolve_context: ResolveContext) -> QueryModifier:
        """Resolve keyword arguments."""
        modifier = QueryModifier()
        
        for key, value in self.filters.items():
            if key in resolve_context.custom_filters:
                # Handle custom filters
                modifier = self._resolve_custom_kwarg(resolve_context, key, value, resolve_context.table)
            else:
                # Handle regular filters
                modifier = self._resolve_regular_kwarg(resolve_context, key, value, resolve_context.table)
        
        return modifier

    def _resolve_children(self, resolve_context: ResolveContext) -> QueryModifier:
        """Resolve child expressions."""
        modifier = QueryModifier()
        
        for child in self.children:
            child_modifier = child.resolve(resolve_context)
            modifier = modifier.combine(child_modifier, self.join_type)
        
        return modifier

    def resolve(
        self,
        resolve_context: ResolveContext,
    ) -> QueryModifier:
        """Resolve the Q expression to a query modifier."""
        # Resolve children first
        modifier = self._resolve_children(resolve_context)
        
        # Resolve keyword arguments
        kwargs_modifier = self._resolve_kwargs(resolve_context)
        
        # Combine modifiers
        if modifier and kwargs_modifier:
            modifier = modifier.combine(kwargs_modifier, self.join_type)
        elif kwargs_modifier:
            modifier = kwargs_modifier
        
        # Apply negation if needed
        if self._is_negated:
            modifier = modifier.negate()
        
        return modifier


class Function(Expression):
    """
    Function/Aggregate base.
    """

    __slots__ = ("field", "field_object", "default_values")

    def __init__(
        self, field: Union[str, F, CombinedExpression, 'Function'], *default_values: Any
    ) -> None:
        """Initialize function."""
        self.field = field
        self.field_object = None
        self.default_values = default_values

    def _get_function_field(self, field: Union[str, F, CombinedExpression, 'Function'], *default_values) -> str:
        """Get function field SQL."""
        if isinstance(field, str):
            return field
        elif isinstance(field, F):
            return field.name
        elif isinstance(field, CombinedExpression):
            return field.resolve(ResolveContext(None, "", {}, {})).term
        elif isinstance(field, 'Function'):
            return field.resolve(ResolveContext(None, "", {}, {})).term
        else:
            return str(field)

    def _resolve_nested_field(self, resolve_context: ResolveContext, field: str) -> ResolveResult:
        """Resolve nested field."""
        # This would be implemented with actual nested field resolution
        return ResolveResult(term=field)

    def _resolve_default_values(self, resolve_context: ResolveContext) -> Iterator[Any]:
        """Resolve default values."""
        for value in self.default_values:
            if isinstance(value, Expression):
                yield value.resolve(resolve_context).term
            else:
                yield value

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        """Resolve function to SQL."""
        # This would be implemented with actual function resolution
        field_sql = self._get_function_field(self.field, *self.default_values)
        return ResolveResult(term=f"FUNCTION({field_sql})")


class Aggregate(Function):
    """
    Base for SQL Aggregates.
    """

    def __init__(
        self,
        field: str | F | CombinedExpression,
        *default_values: Any,
        distinct: bool = False,
        _filter: Q | None = None,
    ) -> None:
        """Initialize aggregate."""
        super().__init__(field, *default_values)
        self.distinct = distinct
        self._filter = _filter

    def _get_function_field(
        self, field: str | F | CombinedExpression, *default_values
    ) -> str:
        """Get aggregate function field SQL."""
        field_sql = super()._get_function_field(field, *default_values)
        if self.distinct:
            return f"DISTINCT {field_sql}"
        return field_sql

    def _resolve_nested_field(self, resolve_context: ResolveContext, field: str) -> ResolveResult:
        """Resolve nested field for aggregate."""
        # This would be implemented with actual nested field resolution
        return ResolveResult(term=field)


class _WhenThen:
    """When-then clause for CASE expressions."""
    
    def __init__(self, when: str, then: str) -> None:
        self.when = when
        self.then = then

    def get_sql(self) -> str:
        """Get SQL for when-then clause."""
        return f"WHEN {self.when} THEN {self.then}"


class When(Expression):
    """When clause for CASE expressions."""
    
    def __init__(
        self,
        *args: Q,
        then: Union[str, F, CombinedExpression, 'Function'],
        negate: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize when clause."""
        self.q_objects = list(args)
        self.then = then
        self.negate = negate
        self.kwargs = kwargs

    def _resolve_q_objects(self) -> list[Q]:
        """Resolve Q objects."""
        q_objects = []
        
        # Add Q objects from args
        for q_obj in self.q_objects:
            if self.negate:
                q_obj = ~q_obj
            q_objects.append(q_obj)
        
        # Add Q object from kwargs
        if self.kwargs:
            q_obj = Q(**self.kwargs)
            if self.negate:
                q_obj = ~q_obj
            q_objects.append(q_obj)
        
        return q_objects

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        """Resolve when clause."""
        # This would be implemented with actual when clause resolution
        when_sql = "condition"  # Placeholder
        then_sql = str(self.then) if not isinstance(self.then, Expression) else self.then.resolve(resolve_context).term
        
        return ResolveResult(term=f"WHEN {when_sql} THEN {then_sql}")


class Case(Expression):
    """CASE expression."""
    
    def __init__(
        self,
        *args: When,
        default: Union[str, F, CombinedExpression, 'Function', None] = None,
    ) -> None:
        """Initialize case expression."""
        self.whens = list(args)
        self.default = default

    def resolve(self, resolve_context: ResolveContext) -> ResolveResult:
        """Resolve case expression."""
        # This would be implemented with actual case expression resolution
        when_clauses = []
        for when in self.whens:
            when_result = when.resolve(resolve_context)
            when_clauses.append(when_result.term)
        
        case_sql = f"CASE {' '.join(when_clauses)}"
        
        if self.default is not None:
            default_sql = str(self.default) if not isinstance(self.default, Expression) else self.default.resolve(resolve_context).term
            case_sql += f" ELSE {default_sql}"
        
        case_sql += " END"
        
        return ResolveResult(term=case_sql) 

"""
Advanced SQL expressions and query building for OxenORM
"""

import json
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from .exceptions import ValidationError

if TYPE_CHECKING:
    from .queryset import AwaitableQuery

class WindowFunction:
    """Window function support for advanced analytics"""
    
    def __init__(self, function: str, partition_by: Optional[List[str]] = None, 
                 order_by: Optional[List[str]] = None, frame: Optional[str] = None):
        self.function = function
        self.partition_by = partition_by or []
        self.order_by = order_by or []
        self.frame = frame
    
    def to_sql(self) -> str:
        sql = f"{self.function}()"
        if self.partition_by or self.order_by or self.frame:
            sql += " OVER ("
            if self.partition_by:
                sql += f"PARTITION BY {', '.join(self.partition_by)}"
            if self.order_by:
                if self.partition_by:
                    sql += " "
                sql += f"ORDER BY {', '.join(self.order_by)}"
            if self.frame:
                if self.partition_by or self.order_by:
                    sql += " "
                sql += self.frame
            sql += ")"
        return sql

class CommonTableExpression:
    """Common Table Expression (CTE) support"""
    
    def __init__(self, name: str, query: 'AwaitableQuery', recursive: bool = False):
        self.name = name
        self.query = query
        self.recursive = recursive
    
    def to_sql(self) -> str:
        recursive_clause = "RECURSIVE " if self.recursive else ""
        return f"{recursive_clause}{self.name} AS ({self.query.to_sql()})"

class FullTextSearch:
    """Full-text search support"""
    
    def __init__(self, columns: List[str], search_term: str, 
                 language: Optional[str] = None, rank_function: str = "ts_rank"):
        self.columns = columns
        self.search_term = search_term
        self.language = language
        self.rank_function = rank_function
    
    def to_sql(self) -> str:
        columns_str = ", ".join(self.columns)
        language_clause = f"'{self.language}'" if self.language else "simple"
        return f"{self.rank_function}(to_tsvector({language_clause}, {columns_str}), plainto_tsquery({language_clause}, '{self.search_term}'))"

class JSONPathQuery:
    """JSON path query support for PostgreSQL JSONB"""
    
    def __init__(self, json_column: str, path: str, operator: str = "->"):
        self.json_column = json_column
        self.path = path
        self.operator = operator
    
    def to_sql(self) -> str:
        return f"{self.json_column} {self.operator} '{self.path}'"
    
    @classmethod
    def contains(cls, json_column: str, path: str, value: Any) -> str:
        """JSON contains operator"""
        return f"{json_column} @> '{{\"{path}\": {json.dumps(value)}}}'"
    
    @classmethod
    def exists(cls, json_column: str, path: str) -> str:
        """JSON exists operator"""
        return f"{json_column} ? '{path}'"

class ArrayOperation:
    """Array operation support"""
    
    def __init__(self, array_column: str, operation: str, value: Any):
        self.array_column = array_column
        self.operation = operation
        self.value = value
    
    def to_sql(self) -> str:
        if self.operation == "contains":
            return f"'{self.value}' = ANY({self.array_column})"
        elif self.operation == "overlaps":
            return f"{self.array_column} && ARRAY[{self.value}]"
        elif self.operation == "length":
            return f"array_length({self.array_column}, 1)"
        elif self.operation == "append":
            return f"{self.array_column} || ARRAY[{self.value}]"
        elif self.operation == "remove":
            return f"array_remove({self.array_column}, {self.value})"
        else:
            raise ValidationError(f"Unsupported array operation: {self.operation}")

class CaseWhen:
    """Enhanced CASE WHEN expression with multiple conditions"""
    
    def __init__(self):
        self.conditions: List[Dict[str, Any]] = []
        self.else_value: Optional[Any] = None
    
    def when(self, condition: str, value: Any) -> 'CaseWhen':
        """Add a WHEN condition"""
        self.conditions.append({"condition": condition, "value": value})
        return self
    
    def else_(self, value: Any) -> 'CaseWhen':
        """Add ELSE clause"""
        self.else_value = value
        return self
    
    def to_sql(self) -> str:
        if not self.conditions:
            raise ValidationError("CASE WHEN must have at least one condition")
        
        sql = "CASE"
        for condition in self.conditions:
            sql += f" WHEN {condition['condition']} THEN {condition['value']}"
        
        if self.else_value is not None:
            sql += f" ELSE {self.else_value}"
        
        sql += " END"
        return sql

class Subquery:
    """Subquery support"""
    
    def __init__(self, query: 'AwaitableQuery', alias: Optional[str] = None):
        self.query = query
        self.alias = alias
    
    def to_sql(self) -> str:
        sql = f"({self.query.to_sql()})"
        if self.alias:
            sql += f" AS {self.alias}"
        return sql

class AggregateFunction:
    """Enhanced aggregate function support"""
    
    def __init__(self, function: str, column: str, distinct: bool = False, 
                 filter_condition: Optional[str] = None):
        self.function = function
        self.column = column
        self.distinct = distinct
        self.filter_condition = filter_condition
    
    def to_sql(self) -> str:
        distinct_clause = "DISTINCT " if self.distinct else ""
        sql = f"{self.function}({distinct_clause}{self.column})"
        
        if self.filter_condition:
            sql += f" FILTER (WHERE {self.filter_condition})"
        
        return sql

class DateFunction:
    """Date and time function support"""
    
    def __init__(self, function: str, column: str, interval: Optional[str] = None):
        self.function = function
        self.column = column
        self.interval = interval
    
    def to_sql(self) -> str:
        if self.interval:
            return f"{self.function}({self.column}, INTERVAL '{self.interval}')"
        return f"{self.function}({self.column})"
    
    @classmethod
    def date_trunc(cls, column: str, precision: str) -> str:
        """Date truncation function"""
        return f"date_trunc('{precision}', {column})"
    
    @classmethod
    def extract(cls, field: str, column: str) -> str:
        """Extract date/time field"""
        return f"EXTRACT({field} FROM {column})"

class StringFunction:
    """String function support"""
    
    def __init__(self, function: str, column: str, *args):
        self.function = function
        self.column = column
        self.args = args
    
    def to_sql(self) -> str:
        args_str = ", ".join([str(arg) for arg in self.args])
        return f"{self.function}({self.column}{', ' + args_str if args_str else ''})"
    
    @classmethod
    def concat(cls, *columns: str) -> str:
        """String concatenation"""
        return f"CONCAT({', '.join(columns)})"
    
    @classmethod
    def substring(cls, column: str, start: int, length: Optional[int] = None) -> str:
        """Substring function"""
        if length:
            return f"SUBSTRING({column} FROM {start} FOR {length})"
        return f"SUBSTRING({column} FROM {start})"

class MathFunction:
    """Mathematical function support"""
    
    def __init__(self, function: str, column: str, *args):
        self.function = function
        self.column = column
        self.args = args
    
    def to_sql(self) -> str:
        args_str = ", ".join([str(arg) for arg in self.args])
        return f"{self.function}({self.column}{', ' + args_str if args_str else ''})"
    
    @classmethod
    def round(cls, column: str, decimals: int = 0) -> str:
        """Round function"""
        return f"ROUND({column}, {decimals})"
    
    @classmethod
    def abs(cls, column: str) -> str:
        """Absolute value function"""
        return f"ABS({column})" 