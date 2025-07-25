"""
Exception classes for OxenORM

This module defines all the exception types used by OxenORM.
"""

from __future__ import annotations

from typing import Any, Optional


class OxenError(Exception):
    """Base exception class for OxenORM."""
    
    def __init__(self, message: str, *args: Any) -> None:
        super().__init__(message, *args)
        self.message = message


class ConfigurationError(OxenError):
    """Raised when there's a configuration error."""
    pass


class ConnectionError(OxenError):
    """Raised when there's a database connection error."""
    pass


class ValidationError(OxenError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None) -> None:
        super().__init__(message)
        self.field = field
        self.value = value


class IntegrityError(OxenError):
    """Raised when database integrity constraints are violated."""
    pass


class DoesNotExist(OxenError):
    """Raised when a requested object does not exist."""
    pass


class MultipleObjectsReturned(OxenError):
    """Raised when a query that should return one object returns multiple."""
    pass


class IncompleteInstanceError(OxenError):
    """Raised when a model instance is incomplete or partially loaded."""
    pass


class OperationalError(OxenError):
    """Raised when there's an operational error with the database."""
    pass


class TransactionError(OxenError):
    """Raised when there's a transaction-related error."""
    pass


class MigrationError(OxenError):
    """Raised when there's a migration-related error."""
    pass


class QueryError(OxenError):
    """Raised when there's a query-related error."""
    pass


class FieldError(OxenError):
    """Raised when there's a field-related error."""
    pass


class ModelError(OxenError):
    """Raised when there's a model-related error."""
    pass


class ParamsError(OxenError):
    """Raised when there's an error with query parameters."""
    pass 