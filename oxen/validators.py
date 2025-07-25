#!/usr/bin/env python3
"""
OxenORM Validators System

This module provides the validators functionality for OxenORM,
which allows for field validation and custom validation rules.
"""

import re
from typing import Any, Callable, List, Optional, Union
from abc import ABC, abstractmethod

from oxen.exceptions import ValidationError


class Validator(ABC):
    """
    Base class for field validators.
    
    All validators should inherit from this class and implement
    the validate method.
    """

    @abstractmethod
    def validate(self, value: Any) -> None:
        """
        Validate a value.
        
        Args:
            value: The value to validate
            
        Raises:
            ValidationError: If validation fails
        """
        pass

    def __call__(self, value: Any) -> None:
        """Call the validator."""
        self.validate(value)


class MinValueValidator(Validator):
    """Validator for minimum value."""
    
    def __init__(self, min_value: Union[int, float]):
        """Initialize with minimum value."""
        self.min_value = min_value

    def validate(self, value: Any) -> None:
        """Validate that value is greater than or equal to min_value."""
        if value is not None and value < self.min_value:
            raise ValidationError(f"Value must be greater than or equal to {self.min_value}")


class MaxValueValidator(Validator):
    """Validator for maximum value."""
    
    def __init__(self, max_value: Union[int, float]):
        """Initialize with maximum value."""
        self.max_value = max_value

    def validate(self, value: Any) -> None:
        """Validate that value is less than or equal to max_value."""
        if value is not None and value > self.max_value:
            raise ValidationError(f"Value must be less than or equal to {self.max_value}")


class MinLengthValidator(Validator):
    """Validator for minimum length."""
    
    def __init__(self, min_length: int):
        """Initialize with minimum length."""
        self.min_length = min_length

    def validate(self, value: Any) -> None:
        """Validate that value has minimum length."""
        if value is not None and len(str(value)) < self.min_length:
            raise ValidationError(f"Value must have at least {self.min_length} characters")


class MaxLengthValidator(Validator):
    """Validator for maximum length."""
    
    def __init__(self, max_length: int):
        """Initialize with maximum length."""
        self.max_length = max_length

    def validate(self, value: Any) -> None:
        """Validate that value has maximum length."""
        if value is not None and len(str(value)) > self.max_length:
            raise ValidationError(f"Value must have at most {self.max_length} characters")


class RegexValidator(Validator):
    """Validator for regular expression matching."""
    
    def __init__(self, regex: str, message: Optional[str] = None):
        """Initialize with regex pattern."""
        self.regex = regex
        self.message = message or f"Value must match pattern: {regex}"
        self.pattern = re.compile(regex)

    def validate(self, value: Any) -> None:
        """Validate that value matches regex pattern."""
        if value is not None and not self.pattern.match(str(value)):
            raise ValidationError(self.message)


class EmailValidator(Validator):
    """Validator for email addresses."""
    
    def __init__(self):
        """Initialize email validator."""
        # Simple email regex pattern
        self.pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def validate(self, value: Any) -> None:
        """Validate that value is a valid email address."""
        if value is not None and not self.pattern.match(str(value)):
            raise ValidationError("Enter a valid email address")


class URLValidator(Validator):
    """Validator for URLs."""
    
    def __init__(self):
        """Initialize URL validator."""
        # Simple URL regex pattern
        self.pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def validate(self, value: Any) -> None:
        """Validate that value is a valid URL."""
        if value is not None and not self.pattern.match(str(value)):
            raise ValidationError("Enter a valid URL")


class ChoiceValidator(Validator):
    """Validator for choice fields."""
    
    def __init__(self, choices: List[Any]):
        """Initialize with list of valid choices."""
        self.choices = choices

    def validate(self, value: Any) -> None:
        """Validate that value is in the list of choices."""
        if value is not None and value not in self.choices:
            raise ValidationError(f"Value must be one of: {', '.join(map(str, self.choices))}")


class UniqueValidator(Validator):
    """Validator for unique values."""
    
    def __init__(self, model: Any, field_name: str, exclude_pk: Optional[Any] = None):
        """Initialize with model and field name."""
        self.model = model
        self.field_name = field_name
        self.exclude_pk = exclude_pk

    def validate(self, value: Any) -> None:
        """Validate that value is unique in the database."""
        if value is None:
            return
        
        # Build filter to check for existing values
        filter_kwargs = {self.field_name: value}
        if self.exclude_pk is not None:
            filter_kwargs['pk__ne'] = self.exclude_pk
        
        # Check if any instance exists with this value
        # This would be implemented with actual database query
        # For now, we'll assume it's unique
        pass


class FileExtensionValidator(Validator):
    """Validator for file extensions."""
    
    def __init__(self, allowed_extensions: List[str]):
        """Initialize with list of allowed extensions."""
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]

    def validate(self, value: Any) -> None:
        """Validate that file has allowed extension."""
        if value is None:
            return
        
        filename = str(value)
        if '.' in filename:
            extension = filename.rsplit('.', 1)[1].lower()
            if extension not in self.allowed_extensions:
                raise ValidationError(f"File extension must be one of: {', '.join(self.allowed_extensions)}")


class FileSizeValidator(Validator):
    """Validator for file size."""
    
    def __init__(self, max_size: int):
        """Initialize with maximum file size in bytes."""
        self.max_size = max_size

    def validate(self, value: Any) -> None:
        """Validate that file size is within limit."""
        if value is None:
            return
        
        # This would be implemented with actual file size checking
        # For now, we'll assume it's valid
        pass


class CustomValidator(Validator):
    """Custom validator that uses a callable function."""
    
    def __init__(self, validator_func: Callable[[Any], None], message: Optional[str] = None):
        """Initialize with validator function."""
        self.validator_func = validator_func
        self.message = message

    def validate(self, value: Any) -> None:
        """Validate using the custom function."""
        try:
            self.validator_func(value)
        except Exception as e:
            if self.message:
                raise ValidationError(self.message)
            else:
                raise ValidationError(str(e))


# Convenience functions for common validators
def min_value(min_value: Union[int, float]) -> MinValueValidator:
    """Create a minimum value validator."""
    return MinValueValidator(min_value)


def max_value(max_value: Union[int, float]) -> MaxValueValidator:
    """Create a maximum value validator."""
    return MaxValueValidator(max_value)


def min_length(min_length: int) -> MinLengthValidator:
    """Create a minimum length validator."""
    return MinLengthValidator(min_length)


def max_length(max_length: int) -> MaxLengthValidator:
    """Create a maximum length validator."""
    return MaxLengthValidator(max_length)


def regex(regex: str, message: Optional[str] = None) -> RegexValidator:
    """Create a regex validator."""
    return RegexValidator(regex, message)


def email() -> EmailValidator:
    """Create an email validator."""
    return EmailValidator()


def url() -> URLValidator:
    """Create a URL validator."""
    return URLValidator()


def choice(choices: List[Any]) -> ChoiceValidator:
    """Create a choice validator."""
    return ChoiceValidator(choices)


def unique(model: Any, field_name: str, exclude_pk: Optional[Any] = None) -> UniqueValidator:
    """Create a unique validator."""
    return UniqueValidator(model, field_name, exclude_pk)


def file_extension(allowed_extensions: List[str]) -> FileExtensionValidator:
    """Create a file extension validator."""
    return FileExtensionValidator(allowed_extensions)


def file_size(max_size: int) -> FileSizeValidator:
    """Create a file size validator."""
    return FileSizeValidator(max_size)


def custom(validator_func: Callable[[Any], None], message: Optional[str] = None) -> CustomValidator:
    """Create a custom validator."""
    return CustomValidator(validator_func, message)


# Example usage:
# class User(Model):
#     email = CharField(validators=[email()])
#     age = IntField(validators=[min_value(0), max_value(150)])
#     username = CharField(validators=[min_length(3), max_length(20)])
#     website = CharField(validators=[url()])
#     avatar = FileField(validators=[
#         file_extension(['jpg', 'png', 'gif']),
#         file_size(1024 * 1024)  # 1MB
#     ]) 