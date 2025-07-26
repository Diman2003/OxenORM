"""
Base field class for OxenORM
"""

from typing import Any, Optional, Type, Union, Callable
from abc import ABC, abstractmethod
import re
from ..exceptions import ValidationError

class Field(ABC):
    """
    Base field class for OxenORM models
    """
    
    def __init__(
        self,
        primary_key: bool = False,
        auto_increment: bool = False,
        null: bool = False,
        blank: bool = False,
        default: Optional[Any] = None,
        unique: bool = False,
        db_index: bool = False,
        db_column: Optional[str] = None,
        validators: Optional[list[Callable]] = None,
        choices: Optional[list[tuple]] = None,
        help_text: Optional[str] = None,
        verbose_name: Optional[str] = None,
        **kwargs
    ):
        self.primary_key = primary_key
        self.auto_increment = auto_increment
        self.null = null
        self.blank = blank
        self.default = default
        self.unique = unique
        self.db_index = db_index
        self.db_column = db_column
        self.validators = validators or []
        self.choices = choices
        self.help_text = help_text
        self.verbose_name = verbose_name
        
        # Internal attributes
        self.name: Optional[str] = None
        self.model: Optional[Type] = None
        self.model_field_name: Optional[str] = None
        
        # Default attributes for compatibility
        self.generated = False
        self.has_db_field = True
        self.source_field = None
        self.skip_to_python_if_native = False
        
        # Store additional kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def validate(self, value: Any) -> Any:
        """Validate and return the field value"""
        # Handle None/null values
        if value is None:
            if not self.null:
                raise ValidationError(f"Field '{self.name}' cannot be null")
            return None
        
        # Handle blank values for string fields
        if isinstance(value, str) and not value.strip() and not self.blank:
            raise ValidationError(f"Field '{self.name}' cannot be blank")
        
        # Validate choices if specified
        if self.choices and value not in [choice[0] for choice in self.choices]:
            valid_choices = [choice[0] for choice in self.choices]
            raise ValidationError(f"Value '{value}' is not a valid choice. Valid choices: {valid_choices}")
        
        # Run custom validators
        for validator in self.validators:
            validator(value)
        
        # Run field-specific validation
        return self._validate(value)
    
    @abstractmethod
    def _validate(self, value: Any) -> Any:
        """Field-specific validation"""
        pass
    
    @abstractmethod
    def to_db_value(self, value: Any) -> Any:
        """Convert Python value to database value"""
        pass
    
    @abstractmethod
    def from_db_value(self, value: Any) -> Any:
        """Convert database value to Python value"""
        pass
    
    def get_default(self) -> Any:
        """Get the default value for this field"""
        if callable(self.default):
            return self.default()
        return self.default
    
    def get_db_column(self) -> str:
        """Get the database column name for this field"""
        return self.db_column or self.name
    
    def to_python_value(self, value: Any) -> Any:
        """Convert database value to Python value"""
        return self.from_db_value(value)
    
    def get_sql_type(self) -> str:
        """Get the SQL type for this field"""
        return self._get_sql_type()
    
    @abstractmethod
    def _get_sql_type(self) -> str:
        """Get the SQL type for this field"""
        pass
    
    def __repr__(self) -> str:
        attrs = []
        if self.primary_key:
            attrs.append("primary_key=True")
        if self.null:
            attrs.append("null=True")
        if self.unique:
            attrs.append("unique=True")
        if self.default is not None:
            attrs.append(f"default={repr(self.default)}")
        
        return f"{self.__class__.__name__}({', '.join(attrs)})"
    
    def __str__(self) -> str:
        return self.__repr__()

class AutoField(Field):
    """Auto-incrementing primary key field"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('primary_key', True)
        kwargs.setdefault('auto_increment', True)
        super().__init__(**kwargs)
    
    def _validate(self, value: Any) -> Any:
        if value is not None and not isinstance(value, int):
            raise ValidationError(f"AutoField must be an integer, got {type(value)}")
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return value
    
    def from_db_value(self, value: Any) -> Any:
        return int(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "INTEGER PRIMARY KEY AUTOINCREMENT"

class BigIntegerField(Field):
    """64-bit integer field"""
    
    def _validate(self, value: Any) -> Any:
        if not isinstance(value, int):
            raise ValidationError(f"BigIntegerField must be an integer, got {type(value)}")
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return value
    
    def from_db_value(self, value: Any) -> Any:
        return int(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "BIGINT"

class SmallIntegerField(Field):
    """16-bit integer field"""
    
    def _validate(self, value: Any) -> Any:
        if not isinstance(value, int):
            raise ValidationError(f"SmallIntegerField must be an integer, got {type(value)}")
        if value < -32768 or value > 32767:
            raise ValidationError(f"SmallIntegerField value {value} out of range")
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return value
    
    def from_db_value(self, value: Any) -> Any:
        return int(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "SMALLINT"

class PositiveIntegerField(Field):
    """Positive integer field"""
    
    def _validate(self, value: Any) -> Any:
        if not isinstance(value, int):
            raise ValidationError(f"PositiveIntegerField must be an integer, got {type(value)}")
        if value < 0:
            raise ValidationError(f"PositiveIntegerField value {value} must be positive")
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return value
    
    def from_db_value(self, value: Any) -> Any:
        return int(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "INTEGER"

class PositiveSmallIntegerField(Field):
    """Positive small integer field (0-32767)"""
    
    def _validate(self, value: Any) -> Any:
        if not isinstance(value, int):
            raise ValidationError(f"PositiveSmallIntegerField must be an integer, got {type(value)}")
        if value < 0 or value > 32767:
            raise ValidationError(f"PositiveSmallIntegerField value {value} out of range (0-32767)")
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return value
    
    def from_db_value(self, value: Any) -> Any:
        return int(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "SMALLINT" 