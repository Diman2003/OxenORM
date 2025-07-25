#!/usr/bin/env python3
"""
OxenORM Filters System

This module provides the filters functionality for OxenORM,
including filter information dictionaries and filter resolution.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

from oxen.fields.base import Field


@dataclass
class FilterInfoDict:
    """Dictionary containing filter information."""
    field: Field
    lookup: str
    operator: str
    value: Any
    function: Optional[Callable] = None


def get_filters_for_field(field: Field) -> Dict[str, FilterInfoDict]:
    """
    Get available filters for a field.
    
    Args:
        field: Field to get filters for
        
    Returns:
        Dictionary of filter name to FilterInfoDict
    """
    filters = {}
    
    # Basic comparison filters
    filters['exact'] = FilterInfoDict(field=field, lookup='exact', operator='=', value=None)
    filters['iexact'] = FilterInfoDict(field=field, lookup='iexact', operator='ILIKE', value=None)
    filters['contains'] = FilterInfoDict(field=field, lookup='contains', operator='LIKE', value=None)
    filters['icontains'] = FilterInfoDict(field=field, lookup='icontains', operator='ILIKE', value=None)
    filters['startswith'] = FilterInfoDict(field=field, lookup='startswith', operator='LIKE', value=None)
    filters['istartswith'] = FilterInfoDict(field=field, lookup='istartswith', operator='ILIKE', value=None)
    filters['endswith'] = FilterInfoDict(field=field, lookup='endswith', operator='LIKE', value=None)
    filters['iendswith'] = FilterInfoDict(field=field, lookup='iendswith', operator='ILIKE', value=None)
    
    # Numeric filters
    if hasattr(field, 'field_type') and field.field_type in (int, float):
        filters['gt'] = FilterInfoDict(field=field, lookup='gt', operator='>', value=None)
        filters['gte'] = FilterInfoDict(field=field, lookup='gte', operator='>=', value=None)
        filters['lt'] = FilterInfoDict(field=field, lookup='lt', operator='<', value=None)
        filters['lte'] = FilterInfoDict(field=field, lookup='lte', operator='<=', value=None)
    
    # List filters
    filters['in'] = FilterInfoDict(field=field, lookup='in', operator='IN', value=None)
    filters['not_in'] = FilterInfoDict(field=field, lookup='not_in', operator='NOT IN', value=None)
    
    # Null filters
    filters['isnull'] = FilterInfoDict(field=field, lookup='isnull', operator='IS NULL', value=None)
    filters['not_isnull'] = FilterInfoDict(field=field, lookup='not_isnull', operator='IS NOT NULL', value=None)
    
    # Range filters
    filters['range'] = FilterInfoDict(field=field, lookup='range', operator='BETWEEN', value=None)
    
    # Date filters (if applicable)
    if hasattr(field, 'field_type') and 'datetime' in str(field.field_type).lower():
        filters['year'] = FilterInfoDict(field=field, lookup='year', operator='EXTRACT(YEAR FROM)', value=None)
        filters['month'] = FilterInfoDict(field=field, lookup='month', operator='EXTRACT(MONTH FROM)', value=None)
        filters['day'] = FilterInfoDict(field=field, lookup='day', operator='EXTRACT(DAY FROM)', value=None)
        filters['week'] = FilterInfoDict(field=field, lookup='week', operator='EXTRACT(WEEK FROM)', value=None)
        filters['week_day'] = FilterInfoDict(field=field, lookup='week_day', operator='EXTRACT(DOW FROM)', value=None)
        filters['quarter'] = FilterInfoDict(field=field, lookup='quarter', operator='EXTRACT(QUARTER FROM)', value=None)
        filters['hour'] = FilterInfoDict(field=field, lookup='hour', operator='EXTRACT(HOUR FROM)', value=None)
        filters['minute'] = FilterInfoDict(field=field, lookup='minute', operator='EXTRACT(MINUTE FROM)', value=None)
        filters['second'] = FilterInfoDict(field=field, lookup='second', operator='EXTRACT(SECOND FROM)', value=None)
    
    # JSON filters (if applicable)
    if hasattr(field, 'field_type') and 'json' in str(field.field_type).lower():
        filters['json_contains'] = FilterInfoDict(field=field, lookup='json_contains', operator='JSON_CONTAINS', value=None)
        filters['json_extract'] = FilterInfoDict(field=field, lookup='json_extract', operator='JSON_EXTRACT', value=None)
    
    return filters


def resolve_filter_lookup(field: Field, lookup: str, value: Any) -> FilterInfoDict:
    """
    Resolve a filter lookup to a FilterInfoDict.
    
    Args:
        field: Field to filter on
        lookup: Lookup type (e.g., 'exact', 'contains', 'gt')
        value: Value to filter by
        
    Returns:
        FilterInfoDict with resolved filter information
    """
    filters = get_filters_for_field(field)
    
    if lookup not in filters:
        raise ValueError(f"Unknown lookup '{lookup}' for field {field.name}")
    
    filter_info = filters[lookup]
    filter_info.value = value
    
    return filter_info


def build_filter_sql(filter_info: FilterInfoDict, field_name: str) -> str:
    """
    Build SQL for a filter.
    
    Args:
        filter_info: Filter information
        field_name: Name of the field to filter on
        
    Returns:
        SQL condition string
    """
    operator = filter_info.operator
    value = filter_info.value
    
    if operator in ('LIKE', 'ILIKE'):
        if operator == 'LIKE':
            return f"{field_name} LIKE '%{value}%'"
        else:
            return f"LOWER({field_name}) LIKE LOWER('%{value}%')"
    
    elif operator == 'startswith':
        return f"{field_name} LIKE '{value}%'"
    
    elif operator == 'istartswith':
        return f"LOWER({field_name}) LIKE LOWER('{value}%')"
    
    elif operator == 'endswith':
        return f"{field_name} LIKE '%{value}'"
    
    elif operator == 'iendswith':
        return f"LOWER({field_name}) LIKE LOWER('%{value}')"
    
    elif operator == 'IN':
        if isinstance(value, (list, tuple)):
            value_list = [f"'{v}'" if isinstance(v, str) else str(v) for v in value]
            return f"{field_name} IN ({', '.join(value_list)})"
        else:
            return f"{field_name} = '{value}'"
    
    elif operator == 'NOT IN':
        if isinstance(value, (list, tuple)):
            value_list = [f"'{v}'" if isinstance(v, str) else str(v) for v in value]
            return f"{field_name} NOT IN ({', '.join(value_list)})"
        else:
            return f"{field_name} != '{value}'"
    
    elif operator == 'IS NULL':
        return f"{field_name} IS NULL"
    
    elif operator == 'IS NOT NULL':
        return f"{field_name} IS NOT NULL"
    
    elif operator == 'BETWEEN':
        if isinstance(value, (list, tuple)) and len(value) == 2:
            min_val, max_val = value
            return f"{field_name} BETWEEN {min_val} AND {max_val}"
        else:
            raise ValueError("Range filter requires a list or tuple with exactly 2 values")
    
    elif operator.startswith('EXTRACT'):
        # Date/time extraction
        return f"{operator} {field_name} = {value}"
    
    elif operator == 'JSON_CONTAINS':
        return f"JSON_CONTAINS({field_name}, '{value}')"
    
    elif operator == 'JSON_EXTRACT':
        return f"JSON_EXTRACT({field_name}, '{value}')"
    
    else:
        # Default comparison
        if isinstance(value, str):
            return f"{field_name} {operator} '{value}'"
        else:
            return f"{field_name} {operator} {value}"


def parse_filter_lookup(lookup: str) -> tuple[str, str]:
    """
    Parse a filter lookup string.
    
    Args:
        lookup: Lookup string (e.g., "field__exact", "field__contains")
        
    Returns:
        Tuple of (field_name, lookup_type)
    """
    if '__' not in lookup:
        return lookup, 'exact'
    
    parts = lookup.split('__')
    field_name = '__'.join(parts[:-1])
    lookup_type = parts[-1]
    
    return field_name, lookup_type


def build_complex_filter(filters: Dict[str, Any], model: Any) -> List[str]:
    """
    Build complex filter conditions from a dictionary.
    
    Args:
        filters: Dictionary of field lookups to values
        model: Model class
        
    Returns:
        List of SQL conditions
    """
    conditions = []
    
    for lookup, value in filters.items():
        field_name, lookup_type = parse_filter_lookup(lookup)
        
        if field_name not in model._meta.fields_map:
            raise ValueError(f"Field '{field_name}' not found in model {model.__name__}")
        
        field = model._meta.fields_map[field_name]
        filter_info = resolve_filter_lookup(field, lookup_type, value)
        
        sql_condition = build_filter_sql(filter_info, field_name)
        conditions.append(sql_condition)
    
    return conditions


def build_q_filter(q_object: Any, model: Any) -> List[str]:
    """
    Build filter conditions from a Q object.
    
    Args:
        q_object: Q object containing filter conditions
        model: Model class
        
    Returns:
        List of SQL conditions
    """
    # This would be implemented with actual Q object resolution
    # For now, return empty list
    return []


def combine_filter_conditions(conditions: List[str], join_type: str = 'AND') -> str:
    """
    Combine filter conditions with a join type.
    
    Args:
        conditions: List of SQL conditions
        join_type: How to join conditions ('AND' or 'OR')
        
    Returns:
        Combined SQL condition string
    """
    if not conditions:
        return ""
    
    if len(conditions) == 1:
        return conditions[0]
    
    return f" {join_type} ".join(f"({condition})" for condition in conditions) 