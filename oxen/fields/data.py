"""
Data field types for OxenORM
"""

from typing import Any, Optional, Union, List, Tuple, Dict
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

class IntField(Field):
    """32-bit integer field"""
    
    def _validate(self, value: Any) -> Any:
        if not isinstance(value, int):
            raise ValidationError(f"IntField must be an integer, got {type(value)}")
        return value
    
    def to_db_value(self, value: Any) -> Any:
        return int(value) if value is not None else None
    
    def from_db_value(self, value: Any) -> Any:
        return int(value) if value is not None else None
    
    def _get_sql_type(self) -> str:
        return "INTEGER"

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
    
    def __init__(self, auto_generate: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.auto_generate = auto_generate
    
    def _validate(self, value: Any) -> Any:
        if value is None:
            if self.auto_generate:
                import uuid
                return str(uuid.uuid4())
            return None
        
        if isinstance(value, str):
            try:
                import uuid
                uuid.UUID(value)
                return value
            except ValueError:
                raise ValidationError(f"Invalid UUID format: {value}")
        else:
            raise ValidationError(f"UUIDField expects string, got {type(value)}")
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return str(value)

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

class FileField(Field):
    """
    File field for storing and managing file data with Rust backend operations.
    
    Supports file read/write operations, file management, and metadata.
    """
    
    def __init__(self, upload_to: str = "uploads/", max_size: int = 10 * 1024 * 1024, 
                 allowed_extensions: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.upload_to = upload_to
        self.max_size = max_size  # 10MB default
        self.allowed_extensions = allowed_extensions or []
        self.storage_path = None
        
    def to_db_value(self, value, instance):
        """Convert file path or bytes to database storage format."""
        if value is None:
            return None
            
        if isinstance(value, str):
            # File path - read the file
            return self._read_file_bytes(value)
        elif isinstance(value, bytes):
            # Already bytes
            return value
        else:
            raise ValueError(f"FileField expects string path or bytes, got {type(value)}")
    
    def to_python_value(self, value):
        """Convert database value back to file path."""
        if value is None:
            return None
            
        if isinstance(value, bytes):
            # Save to temporary file and return path
            return self._save_temp_file(value)
        return value
    
    def _read_file_bytes(self, file_path: str) -> bytes:
        """Read file using Rust backend."""
        try:
            import oxen_engine
            return oxen_engine.read_file(file_path)
        except ImportError:
            # Fallback to Python
            with open(file_path, 'rb') as f:
                return f.read()
    
    def _save_temp_file(self, data: bytes) -> str:
        """Save bytes to temporary file and return path."""
        import tempfile
        import os
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_to, exist_ok=True)
        
        # Generate unique filename
        import uuid
        filename = f"{uuid.uuid4()}.tmp"
        file_path = os.path.join(self.upload_to, filename)
        
        try:
            import oxen_engine
            oxen_engine.write_file(file_path, data)
        except ImportError:
            # Fallback to Python
            with open(file_path, 'wb') as f:
                f.write(data)
        
        return file_path
    
    def validate(self, value):
        """Validate file data."""
        if value is None:
            return
            
        if isinstance(value, str):
            # Check if file exists
            if not self._file_exists(value):
                raise ValueError(f"File does not exist: {value}")
            
            # Check file size
            file_size = self._get_file_size(value)
            if file_size > self.max_size:
                raise ValueError(f"File too large: {file_size} bytes (max: {self.max_size})")
            
            # Check extension
            if self.allowed_extensions:
                ext = os.path.splitext(value)[1].lower()
                if ext not in self.allowed_extensions:
                    raise ValueError(f"File extension not allowed: {ext}")
        
        elif isinstance(value, bytes):
            # Check size
            if len(value) > self.max_size:
                raise ValueError(f"File too large: {len(value)} bytes (max: {self.max_size})")
    
    def _file_exists(self, path: str) -> bool:
        """Check if file exists using Rust backend."""
        try:
            import oxen_engine
            return oxen_engine.file_exists(path)
        except ImportError:
            return os.path.exists(path)
    
    def _get_file_size(self, path: str) -> int:
        """Get file size using Rust backend."""
        try:
            import oxen_engine
            return oxen_engine.get_file_size(path)
        except ImportError:
            return os.path.getsize(path)
    
    def delete_file(self, file_path: str):
        """Delete file using Rust backend."""
        try:
            import oxen_engine
            oxen_engine.delete_file(file_path)
        except ImportError:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def _validate(self, value: Any) -> Any:
        """Validate file data."""
        if value is None:
            return value
        
        if isinstance(value, str):
            # Check if file exists
            if not self._file_exists(value):
                raise ValidationError(f"File does not exist: {value}")
            
            # Check file size
            file_size = self._get_file_size(value)
            if file_size > self.max_size:
                raise ValidationError(f"File too large: {file_size} bytes (max: {self.max_size})")
            
            # Check extension
            if self.allowed_extensions:
                import os
                ext = os.path.splitext(value)[1].lower()
                if ext not in self.allowed_extensions:
                    raise ValidationError(f"File extension not allowed: {ext}")
        
        elif isinstance(value, bytes):
            # Check size
            if len(value) > self.max_size:
                raise ValidationError(f"File too large: {len(value)} bytes (max: {self.max_size})")
        
        return value
    
    def _get_sql_type(self) -> str:
        """Get SQL type for this field."""
        return "BLOB"
    
    def from_db_value(self, value: Any) -> Any:
        """Convert database value to Python value."""
        return value


class ImageField(FileField):
    """
    Image field for storing and managing image data with Rust backend operations.
    
    Supports image processing, resizing, format conversion, and metadata.
    """
    
    def __init__(self, upload_to: str = "images/", max_size: int = 5 * 1024 * 1024,
                 allowed_formats: List[str] = None, resize_to: Tuple[int, int] = None,
                 create_thumbnail: bool = False, thumbnail_size: int = 150, **kwargs):
        super().__init__(upload_to=upload_to, max_size=max_size, **kwargs)
        self.allowed_formats = allowed_formats or ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        self.resize_to = resize_to
        self.create_thumbnail = create_thumbnail
        self.thumbnail_size = thumbnail_size
    
    def to_db_value(self, value, instance):
        """Convert image path or bytes to database storage format with optional processing."""
        if value is None:
            return None
            
        # Get raw bytes
        if isinstance(value, str):
            data = self._read_file_bytes(value)
        elif isinstance(value, bytes):
            data = value
        else:
            raise ValueError(f"ImageField expects string path or bytes, got {type(value)}")
        
        # Process image if needed
        data = self._process_image(data)
        
        return data
    
    def _process_image(self, data: bytes) -> bytes:
        """Process image using Rust backend."""
        try:
            import oxen_engine
            
            # Resize if specified
            if self.resize_to:
                width, height = self.resize_to
                data = oxen_engine.resize_image(data, width, height)
            
            # Create thumbnail if requested
            if self.create_thumbnail:
                thumbnail_data = oxen_engine.create_thumbnail(data, self.thumbnail_size)
                # Store thumbnail separately (you might want to add a thumbnail field)
                thumbnail_path = self._save_thumbnail(thumbnail_data)
            
            return data
            
        except ImportError:
            # Fallback to Python (basic processing)
            return data
    
    def _save_thumbnail(self, data: bytes) -> str:
        """Save thumbnail to file."""
        import os
        import uuid
        
        thumbnail_dir = os.path.join(self.upload_to, "thumbnails")
        os.makedirs(thumbnail_dir, exist_ok=True)
        
        filename = f"thumb_{uuid.uuid4()}.png"
        file_path = os.path.join(thumbnail_dir, filename)
        
        try:
            import oxen_engine
            oxen_engine.save_image(file_path, data)
        except ImportError:
            with open(file_path, 'wb') as f:
                f.write(data)
        
        return file_path
    
    def get_image_info(self, data: bytes) -> Dict[str, Any]:
        """Get image information using Rust backend."""
        try:
            import oxen_engine
            width, height, format = oxen_engine.get_image_info(data)
            return {
                'width': width,
                'height': height,
                'format': format,
                'size': len(data)
            }
        except ImportError:
            # Fallback to Python
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(data))
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'size': len(data)
            }
    
    def resize_image(self, data: bytes, width: int, height: int) -> bytes:
        """Resize image using Rust backend."""
        try:
            import oxen_engine
            return oxen_engine.resize_image(data, width, height)
        except ImportError:
            # Fallback to Python
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(data))
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            resized.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def blur_image(self, data: bytes, sigma: float = 1.0) -> bytes:
        """Blur image using Rust backend."""
        try:
            import oxen_engine
            return oxen_engine.blur_image(data, sigma)
        except ImportError:
            # Fallback to Python
            from PIL import Image, ImageFilter
            import io
            
            img = Image.open(io.BytesIO(data))
            blurred = img.filter(ImageFilter.GaussianBlur(radius=sigma))
            
            buffer = io.BytesIO()
            blurred.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def brighten_image(self, data: bytes, value: int = 10) -> bytes:
        """Brighten image using Rust backend."""
        try:
            import oxen_engine
            return oxen_engine.brighten_image(data, value)
        except ImportError:
            # Fallback to Python
            from PIL import Image, ImageEnhance
            import io
            
            img = Image.open(io.BytesIO(data))
            enhancer = ImageEnhance.Brightness(img)
            brightened = enhancer.enhance(1.0 + value / 100.0)
            
            buffer = io.BytesIO()
            brightened.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def convert_format(self, data: bytes, format: str) -> bytes:
        """Convert image format using Rust backend."""
        try:
            import oxen_engine
            return oxen_engine.convert_image_format(data, format)
        except ImportError:
            # Fallback to Python
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(data))
            buffer = io.BytesIO()
            img.save(buffer, format=format.upper())
            return buffer.getvalue()
    
    def create_thumbnail(self, data: bytes, max_size: int = 150) -> bytes:
        """Create thumbnail using Rust backend."""
        try:
            import oxen_engine
            return oxen_engine.create_thumbnail(data, max_size)
        except ImportError:
            # Fallback to Python
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(data))
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue() 

class ArrayField(Field):
    """PostgreSQL Array field type"""
    
    def __init__(self, element_type: str = "text", dimensions: int = 1, **kwargs):
        super().__init__(**kwargs)
        self.element_type = element_type
        self.dimensions = dimensions
    
    def _get_sql_type(self) -> str:
        if self.dimensions == 1:
            return f"{self.element_type}[]"
        else:
            return f"{self.element_type}[{','.join([''] * self.dimensions)}]"
    
    def _validate(self, value: Any) -> Any:
        if value is None:
            return value
        
        if not isinstance(value, (list, tuple)):
            raise ValidationError(f"ArrayField expects list or tuple, got {type(value)}")
        
        # Validate array dimensions
        if self.dimensions > 1:
            self._validate_dimensions(value, self.dimensions)
        
        return list(value)
    
    def _validate_dimensions(self, value: Any, expected_dimensions: int, current_dimension: int = 1):
        """Recursively validate array dimensions"""
        if current_dimension > expected_dimensions:
            raise ValidationError(f"Array has too many dimensions: {current_dimension}")
        
        if not isinstance(value, (list, tuple)):
            if current_dimension < expected_dimensions:
                raise ValidationError(f"Expected array at dimension {current_dimension}")
            return
        
        for item in value:
            self._validate_dimensions(item, expected_dimensions, current_dimension + 1)
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return list(value) if isinstance(value, (list, tuple)) else value
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return list(value) if isinstance(value, (list, tuple)) else value

class RangeField(Field):
    """PostgreSQL Range field type"""
    
    def __init__(self, range_type: str = "int4range", **kwargs):
        super().__init__(**kwargs)
        self.range_type = range_type
    
    def _get_sql_type(self) -> str:
        return self.range_type
    
    def _validate(self, value: Any) -> Any:
        if value is None:
            return value
        
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return f"[{value[0]},{value[1]})"
        elif isinstance(value, str):
            return value
        else:
            raise ValidationError(f"RangeField expects list/tuple with 2 elements or string, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return f"[{value[0]},{value[1]})"
        return value
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return str(value)

class HStoreField(Field):
    """PostgreSQL HStore field type for key-value storage"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _get_sql_type(self) -> str:
        return "hstore"
    
    def _validate(self, value: Any) -> Any:
        if value is None:
            return value
        
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            # Parse hstore string format: "key1=>value1,key2=>value2"
            try:
                result = {}
                if value.strip():
                    for pair in value.split(','):
                        if '=>' in pair:
                            key, val = pair.split('=>', 1)
                            result[key.strip()] = val.strip()
                return result
            except Exception:
                raise ValidationError(f"Invalid hstore string format: {value}")
        else:
            raise ValidationError(f"HStoreField expects dict or string, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, dict):
            # Convert dict to hstore string format
            pairs = [f"{k}=>{v}" for k, v in value.items()]
            return ",".join(pairs)
        return value
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return dict(value) if hasattr(value, 'items') else value

class JSONBField(Field):
    """PostgreSQL JSONB field type for efficient JSON storage and querying"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _get_sql_type(self) -> str:
        return "jsonb"
    
    def _validate(self, value: Any) -> Any:
        if value is None:
            return value
        
        if isinstance(value, (dict, list)):
            return value
        elif isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(f"Invalid JSON string: {value}")
        else:
            raise ValidationError(f"JSONBField expects dict, list, or JSON string, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            import json
            return json.dumps(value)
        return value
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return value

class GeometryField(Field):
    """PostGIS Geometry field type for spatial data"""
    
    def __init__(self, geometry_type: str = "POINT", srid: int = 4326, **kwargs):
        super().__init__(**kwargs)
        self.geometry_type = geometry_type.upper()
        self.srid = srid
    
    def _get_sql_type(self) -> str:
        return f"geometry({self.geometry_type},{self.srid})"
    
    def _validate(self, value: Any) -> Any:
        if value is None:
            return value
        
        if isinstance(value, str):
            # WKT (Well-Known Text) format
            return value
        elif isinstance(value, (list, tuple)):
            # Convert coordinates to WKT
            if self.geometry_type == "POINT":
                if len(value) >= 2:
                    return f"POINT({value[0]} {value[1]})"
                else:
                    raise ValidationError("Point requires at least 2 coordinates")
            elif self.geometry_type == "LINESTRING":
                coords = " ".join([f"{coord[0]} {coord[1]}" for coord in value])
                return f"LINESTRING({coords})"
            elif self.geometry_type == "POLYGON":
                # Handle polygon with exterior ring and optional interior rings
                if isinstance(value[0], (list, tuple)):
                    rings = []
                    for ring in value:
                        coords = " ".join([f"{coord[0]} {coord[1]}" for coord in ring])
                        rings.append(f"({coords})")
                    return f"POLYGON({','.join(rings)})"
                else:
                    coords = " ".join([f"{coord[0]} {coord[1]}" for coord in value])
                    return f"POLYGON(({coords}))"
            else:
                raise ValidationError(f"Unsupported geometry type: {self.geometry_type}")
        else:
            raise ValidationError(f"GeometryField expects string (WKT) or coordinates list, got {type(value)}")
    
    def to_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return str(value)
    
    def from_db_value(self, value: Any) -> Any:
        if value is None:
            return None
        return str(value)
    
    @classmethod
    def point(cls, x: float, y: float, srid: int = 4326) -> str:
        """Create a POINT geometry"""
        return f"POINT({x} {y})"
    
    @classmethod
    def linestring(cls, coordinates: List[tuple], srid: int = 4326) -> str:
        """Create a LINESTRING geometry"""
        coords = " ".join([f"{x} {y}" for x, y in coordinates])
        return f"LINESTRING({coords})"
    
    @classmethod
    def polygon(cls, coordinates: List[tuple], srid: int = 4326) -> str:
        """Create a POLYGON geometry"""
        coords = " ".join([f"{x} {y}" for x, y in coordinates])
        return f"POLYGON(({coords}))" 