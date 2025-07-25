#!/usr/bin/env python3
"""
OxenORM Query Utilities

This module provides utility functions and classes for query building
and field resolution in OxenORM.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from oxen.fields.relational import RelationalField


@dataclass
class TableCriterionTuple:
    """Tuple representing table join criteria."""
    table: str
    criterion: str


@dataclass
class QueryModifier:
    """Modifier for query building."""
    where_clauses: List[str] = None
    joins: List[TableCriterionTuple] = None
    annotations: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.where_clauses is None:
            self.where_clauses = []
        if self.joins is None:
            self.joins = []
        if self.annotations is None:
            self.annotations = {}

    def combine(self, other: 'QueryModifier', join_type: str = 'AND') -> 'QueryModifier':
        """Combine with another query modifier."""
        combined = QueryModifier()
        
        # Combine where clauses
        if self.where_clauses and other.where_clauses:
            if join_type == 'AND':
                combined.where_clauses = [f"({clause})" for clause in self.where_clauses + other.where_clauses]
            else:  # OR
                combined.where_clauses = [f"({' OR '.join(self.where_clauses)}) AND ({' OR '.join(other.where_clauses)})"]
        else:
            combined.where_clauses = self.where_clauses + other.where_clauses
        
        # Combine joins
        combined.joins = self.joins + other.joins
        
        # Combine annotations
        combined.annotations = {**self.annotations, **other.annotations}
        
        return combined

    def negate(self) -> 'QueryModifier':
        """Negate the query modifier."""
        negated = QueryModifier()
        negated.where_clauses = [f"NOT ({clause})" for clause in self.where_clauses]
        negated.joins = self.joins
        negated.annotations = self.annotations
        return negated


@dataclass
class Prefetch:
    """Prefetch configuration for related objects."""
    field: str
    to_attr: Optional[str] = None
    queryset: Optional[Any] = None  # Would be QuerySet type
    
    def __init__(self, field: str, to_attr: Optional[str] = None, queryset: Optional[Any] = None):
        self.field = field
        self.to_attr = to_attr or field
        self.queryset = queryset


def expand_lookup_expression(lookup: str) -> List[str]:
    """
    Expand a lookup expression into field parts.
    
    Args:
        lookup: Lookup expression (e.g., "user__profile__name")
        
    Returns:
        List of field parts
    """
    return lookup.split('__')


def resolve_nested_field(model: Any, field_path: str) -> Tuple[Any, str, List[TableCriterionTuple]]:
    """
    Resolve a nested field path to the final model and field.
    
    Args:
        model: Starting model
        field_path: Field path (e.g., "user__profile__name")
        
    Returns:
        Tuple of (final_model, final_field, joins)
    """
    parts = expand_lookup_expression(field_path)
    current_model = model
    joins = []
    
    for i, part in enumerate(parts[:-1]):
        if part not in current_model._meta.fields_map:
            raise ValueError(f"Field '{part}' not found in model {current_model.__name__}")
        
        field_obj = current_model._meta.fields_map[part]
        if not isinstance(field_obj, RelationalField):
            raise ValueError(f"Field '{part}' is not a relational field")
        
        # Get related model
        related_model = field_obj.related_model
        
        # Create join
        join = TableCriterionTuple(
            table=related_model._meta.table_name,
            criterion=f"{current_model._meta.table_name}.{part}_id = {related_model._meta.table_name}.id"
        )
        joins.append(join)
        
        current_model = related_model
    
    final_field = parts[-1]
    if final_field not in current_model._meta.fields_map:
        raise ValueError(f"Field '{final_field}' not found in model {current_model.__name__}")
    
    return current_model, final_field, joins


def get_joins_for_related_field(model: Any, field_name: str) -> List[TableCriterionTuple]:
    """
    Get joins needed for a related field.
    
    Args:
        model: Model class
        field_name: Name of the related field
        
    Returns:
        List of table criterion tuples for joins
    """
    if field_name not in model._meta.fields_map:
        raise ValueError(f"Field '{field_name}' not found in model {model.__name__}")
    
    field_obj = model._meta.fields_map[field_name]
    if not isinstance(field_obj, RelationalField):
        raise ValueError(f"Field '{field_name}' is not a relational field")
    
    related_model = field_obj.related_model
    join = TableCriterionTuple(
        table=related_model._meta.table_name,
        criterion=f"{model._meta.table_name}.{field_name}_id = {related_model._meta.table_name}.id"
    )
    
    return [join]


def resolve_field_json_path(field_path: str) -> Tuple[str, Optional[str]]:
    """
    Resolve a JSON field path.
    
    Args:
        field_path: Field path (e.g., "data__user__name")
        
    Returns:
        Tuple of (field_name, json_path)
    """
    if '__' not in field_path:
        return field_path, None
    
    parts = field_path.split('__')
    field_name = parts[0]
    json_path = '__'.join(parts[1:])
    
    return field_name, json_path


def build_where_clause(field: str, operator: str, value: Any) -> str:
    """
    Build a WHERE clause.
    
    Args:
        field: Field name
        operator: SQL operator (e.g., "=", ">", "LIKE")
        value: Value to compare against
        
    Returns:
        WHERE clause string
    """
    if value is None:
        if operator == '=':
            return f"{field} IS NULL"
        elif operator == '!=':
            return f"{field} IS NOT NULL"
        else:
            return f"{field} {operator} NULL"
    
    if isinstance(value, str):
        return f"{field} {operator} '{value}'"
    else:
        return f"{field} {operator} {value}"


def build_in_clause(field: str, values: List[Any]) -> str:
    """
    Build an IN clause.
    
    Args:
        field: Field name
        values: List of values
        
    Returns:
        IN clause string
    """
    if not values:
        return "1=0"  # Always false
    
    value_list = []
    for value in values:
        if isinstance(value, str):
            value_list.append(f"'{value}'")
        else:
            value_list.append(str(value))
    
    return f"{field} IN ({', '.join(value_list)})"


def build_like_clause(field: str, pattern: str, case_sensitive: bool = True) -> str:
    """
    Build a LIKE clause.
    
    Args:
        field: Field name
        pattern: Pattern to match
        case_sensitive: Whether the match should be case sensitive
        
    Returns:
        LIKE clause string
    """
    if case_sensitive:
        return f"{field} LIKE '{pattern}'"
    else:
        return f"LOWER({field}) LIKE LOWER('{pattern}')"


def build_between_clause(field: str, min_value: Any, max_value: Any) -> str:
    """
    Build a BETWEEN clause.
    
    Args:
        field: Field name
        min_value: Minimum value
        max_value: Maximum value
        
    Returns:
        BETWEEN clause string
    """
    if isinstance(min_value, str):
        min_value = f"'{min_value}'"
    if isinstance(max_value, str):
        max_value = f"'{max_value}'"
    
    return f"{field} BETWEEN {min_value} AND {max_value}"


def escape_sql_value(value: Any) -> str:
    """
    Escape a value for SQL.
    
    Args:
        value: Value to escape
        
    Returns:
        Escaped value string
    """
    if value is None:
        return "NULL"
    elif isinstance(value, str):
        # Simple escaping - in production, use proper SQL escaping
        return f"'{value.replace("'", "''")}'"
    elif isinstance(value, bool):
        return "1" if value else "0"
    else:
        return str(value)


def build_order_clause(field: str, direction: str = "ASC") -> str:
    """
    Build an ORDER BY clause.
    
    Args:
        field: Field name
        direction: Sort direction ("ASC" or "DESC")
        
    Returns:
        ORDER BY clause string
    """
    return f"{field} {direction.upper()}"


def build_group_clause(fields: List[str]) -> str:
    """
    Build a GROUP BY clause.
    
    Args:
        fields: List of field names
        
    Returns:
        GROUP BY clause string
    """
    return ", ".join(fields)


def build_limit_offset_clause(limit: Optional[int] = None, offset: Optional[int] = None) -> str:
    """
    Build LIMIT and OFFSET clauses.
    
    Args:
        limit: Maximum number of rows
        offset: Number of rows to skip
        
    Returns:
        LIMIT/OFFSET clause string
    """
    clauses = []
    
    if limit is not None:
        clauses.append(f"LIMIT {limit}")
    
    if offset is not None:
        clauses.append(f"OFFSET {offset}")
    
    return " ".join(clauses)


def build_select_clause(fields: List[str], table: str) -> str:
    """
    Build a SELECT clause.
    
    Args:
        fields: List of field names
        table: Table name
        
    Returns:
        SELECT clause string
    """
    if not fields:
        return f"SELECT * FROM {table}"
    
    field_list = [f"{table}.{field}" for field in fields]
    return f"SELECT {', '.join(field_list)} FROM {table}"


def build_join_clause(joins: List[TableCriterionTuple]) -> str:
    """
    Build JOIN clauses.
    
    Args:
        joins: List of table criterion tuples
        
    Returns:
        JOIN clause string
    """
    if not joins:
        return ""
    
    join_clauses = []
    for join in joins:
        join_clauses.append(f"JOIN {join.table} ON {join.criterion}")
    
    return " ".join(join_clauses)


def build_where_clauses(where_clauses: List[str]) -> str:
    """
    Build WHERE clauses.
    
    Args:
        where_clauses: List of WHERE conditions
        
    Returns:
        WHERE clause string
    """
    if not where_clauses:
        return ""
    
    return f"WHERE {' AND '.join(where_clauses)}"


def build_complete_query(
    table: str,
    fields: List[str],
    where_clauses: List[str],
    joins: List[TableCriterionTuple],
    order_by: Optional[str] = None,
    group_by: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    distinct: bool = False
) -> str:
    """
    Build a complete SQL query.
    
    Args:
        table: Main table name
        fields: List of fields to select
        where_clauses: List of WHERE conditions
        joins: List of table criterion tuples
        order_by: ORDER BY clause
        group_by: GROUP BY clause
        limit: Maximum number of rows
        offset: Number of rows to skip
        distinct: Whether to use DISTINCT
        
    Returns:
        Complete SQL query string
    """
    # Build SELECT clause
    select_clause = build_select_clause(fields, table)
    if distinct:
        select_clause = select_clause.replace("SELECT", "SELECT DISTINCT")
    
    # Build JOIN clause
    join_clause = build_join_clause(joins)
    
    # Build WHERE clause
    where_clause = build_where_clauses(where_clauses)
    
    # Build GROUP BY clause
    group_clause = f"GROUP BY {group_by}" if group_by else ""
    
    # Build ORDER BY clause
    order_clause = f"ORDER BY {order_by}" if order_by else ""
    
    # Build LIMIT/OFFSET clause
    limit_offset_clause = build_limit_offset_clause(limit, offset)
    
    # Combine all clauses
    query_parts = [select_clause]
    if join_clause:
        query_parts.append(join_clause)
    if where_clause:
        query_parts.append(where_clause)
    if group_clause:
        query_parts.append(group_clause)
    if order_clause:
        query_parts.append(order_clause)
    if limit_offset_clause:
        query_parts.append(limit_offset_clause)
    
    return " ".join(query_parts) 