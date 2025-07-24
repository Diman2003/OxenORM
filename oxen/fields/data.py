"""
Data field types for OxenORM
"""

from typing import Any, Optional, Union
from datetime import datetime, date, time
from decimal import Decimal
import uuid
import json
import re
from .base import Field
from ..exceptions import ValidationError

class CharField(Field):
    """Character field with max length"""
    
    def __init__(self, max_length: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
    
    def _validate(self, value: Any) -> Any:
        if not isinstance(value, str):
            raise ValidationError(f"CharField must be a string, got {type(value)}")
        
        if self.max_length and len(value) > self.max_length:
            raise ValidationError(f"CharField value exceeds max_length of {self.max_length}")
        
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return str(value) if value is not None else None
    
    def from_db_value(self, value: Any) -> Any:
        return str(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        if self.max_length:
            return f"VARCHAR({self.max_length})"
        return "TEXT"

class TextField(Field):
    """Unlimited text field"""
    
    def _validate(self, value: Any) -> Any:
        if not isinstance(value, str):
            raise ValidationError(f"TextField must be a string, got {type(value)}")
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return str(value) if value is not None else None
    
    def from_db_value(self, value: Any) -> Any:
        return str(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "TEXT"

class IntegerField(Field):
    """32-bit integer field"""
    
    def _validate(self, value: Any) -> Any:
        if not isinstance(value, int):
            raise ValidationError(f"IntegerField must be an integer, got {type(value)}")
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return int(value) if value is not None else None
    
    def from_db_value(self, value: Any) -> Any:
        return int(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "INTEGER"

class FloatField(Field):
    """Float field"""
    
    def _validate(self, value: Any) -> Any:
        if not isinstance(value, (int, float)):
            raise ValidationError(f"FloatField must be a number, got {type(value)}")
        return float(value)
    
    def to_db_value(self, value: Any) -> Any:
        return float(value) if value is not None else None
    
    def from_db_value(self, value: Any) -> Any:
        return float(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "REAL"

class DecimalField(Field):
    """Decimal field with precision and scale"""
    
    def __init__(self, max_digits: Optional[int] = None, decimal_places: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places
    
    def _validate(self, value: Any) -> Any:
        if isinstance(value, str):
            value = Decimal(value)
        elif isinstance(value, (int, float)):
            value = Decimal(str(value))
        elif not isinstance(value, Decimal):
            raise ValidationError(f"DecimalField must be a decimal number, got {type(value)}")
        
        # Validate precision
        if self.max_digits:
            digits = len(str(value).replace('.', '').replace('-', ''))
            if digits > self.max_digits:
                raise ValidationError(f"DecimalField value has too many digits (max: {self.max_digits})")
        
        # Validate scale
        if self.decimal_places is not None:
            value = value.quantize(Decimal('0.' + '0' * self.decimal_places))
        
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return str(value) if value is not None else None
    
    def from_db_value(self, value: Any) -> Any:
        return Decimal(str(value)) if value is not None else None
    
    def _get_sql_type(self) -> str:
        if self.max_digits and self.decimal_places:
            return f"DECIMAL({self.max_digits},{self.decimal_places})"
        return "DECIMAL"

class BooleanField(Field):
    """Boolean field"""
    
    def _validate(self, value: Any) -> Any:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            if value.lower() in ('false', '0', 'no', 'off'):
                return False
        if isinstance(value, int):
            return bool(value)
        raise ValidationError(f"BooleanField must be a boolean, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        return 1 if value else 0 if value is not None else None
    
    def from_db_value(self, value: Any) -> Any:
        return bool(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "BOOLEAN"

class DateTimeField(Field):
    """DateTime field"""
    
    def __init__(self, auto_now: bool = False, auto_now_add: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
    
    def _validate(self, value: Any) -> Any:
        if isinstance(value, str):
            # Try to parse common datetime formats
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValidationError(f"DateTimeField cannot parse string: {value}")
        elif isinstance(value, datetime):
            return value
        else:
            raise ValidationError(f"DateTimeField must be a datetime, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value
    
    def _get_sql_type(self) -> str:
        return "DATETIME"

class DateField(Field):
    """Date field"""
    
    def _validate(self, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError(f"DateField cannot parse string: {value}")
        elif isinstance(value, date):
            return value
        elif isinstance(value, datetime):
            return value.date()
        else:
            raise ValidationError(f"DateField must be a date, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, date):
            return value.isoformat()
        return str(value)
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d').date()
        return value
    
    def _get_sql_type(self) -> str:
        return "DATE"

class TimeField(Field):
    """Time field"""
    
    def _validate(self, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%H:%M:%S').time()
            except ValueError:
                raise ValidationError(f"TimeField cannot parse string: {value}")
        elif isinstance(value, time):
            return value
        else:
            raise ValidationError(f"TimeField must be a time, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, time):
            return value.isoformat()
        return str(value)
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return datetime.strptime(value, '%H:%M:%S').time()
        return value
    
    def _get_sql_type(self) -> str:
        return "TIME"

class UUIDField(Field):
    """UUID field"""
    
    def _validate(self, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError:
                raise ValidationError(f"UUIDField cannot parse string: {value}")
        elif isinstance(value, uuid.UUID):
            return value
        else:
            raise ValidationError(f"UUIDField must be a UUID, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        return str(value) if value is not None else None
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return uuid.UUID(value)
        return value
    
    def _get_sql_type(self) -> str:
        return "TEXT"

class JSONField(Field):
    """JSON field"""
    
    def _validate(self, value: Any) -> Any:
        if value is None:
            return None
        # Ensure it's JSON serializable
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            raise ValidationError(f"JSONField value must be JSON serializable, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return json.dumps(value)
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value
    
    def _get_sql_type(self) -> str:
        return "TEXT"

class BinaryField(Field):
    """Binary field for storing bytes"""
    
    def _validate(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode('utf-8')
        raise ValidationError(f"BinaryField must be bytes or string, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        return str(value).encode('utf-8')
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        return str(value).encode('utf-8')
    
    def _get_sql_type(self) -> str:
        return "BLOB"

class EmailField(CharField):
    """Email field with validation"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 254)
        super().__init__(**kwargs)
    
    def _validate(self, value: Any) -> Any:
        value = super()._validate(value)
        if value:
            # Basic email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValidationError(f"Invalid email format: {value}")
        return value

class URLField(CharField):
    """URL field with validation"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 200)
        super().__init__(**kwargs)
    
    def _validate(self, value: Any) -> Any:
        value = super()._validate(value)
        if value:
            # Basic URL validation
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, value):
                raise ValidationError(f"Invalid URL format: {value}")
        return value

class SlugField(CharField):
    """Slug field for URL-friendly strings"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 50)
        super().__init__(**kwargs)
    
    def _validate(self, value: Any) -> Any:
        value = super()._validate(value)
        if value:
            # Slug validation: lowercase, alphanumeric, hyphens only
            slug_pattern = r'^[a-z0-9-]+$'
            if not re.match(slug_pattern, value):
                raise ValidationError(f"Invalid slug format: {value}")
        return value 