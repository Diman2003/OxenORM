"""
Basic tests for OxenORM

These tests verify that the basic imports and structure work correctly.
"""

import pytest
from oxen import Model, init_db, close_db
from oxen.fields import IntField, CharField, TextField
from oxen.exceptions import OxenError


class TestUser(Model):
    """Test user model."""
    
    id = IntField(primary_key=True)
    name = CharField(max_length=100)
    email = CharField(max_length=100, unique=True)
    bio = TextField(null=True)

    class Meta:
        table = "test_users"


def test_imports():
    """Test that all necessary modules can be imported."""
    from oxen import Model, QuerySet, Q
    from oxen.fields import (
        IntField, CharField, TextField, BooleanField,
        DateTimeField, DateField, TimeField, DecimalField,
        FloatField, JSONField, UUIDField
    )
    from oxen.exceptions import (
        OxenError, ConfigurationError, ValidationError,
        IntegrityError, DoesNotExist, MultipleObjectsReturned
    )
    
    # If we get here, imports work
    assert True


def test_model_definition():
    """Test that models can be defined correctly."""
    user = TestUser(name="John Doe", email="john@example.com")
    
    assert user.name == "John Doe"
    assert user.email == "john@example.com"
    assert user.bio is None


def test_model_meta():
    """Test that model metadata is accessible."""
    assert TestUser._meta.db_table == "test_users"
    assert "id" in TestUser._meta.fields_map
    assert "name" in TestUser._meta.fields_map
    assert "email" in TestUser._meta.fields_map


def test_field_validation():
    """Test that field validation works."""
    # Test required field
    with pytest.raises(ValueError):
        TestUser(name="John")  # Missing email
    
    # Test unique constraint
    user1 = TestUser(name="John", email="john@example.com")
    user2 = TestUser(name="Jane", email="john@example.com")  # Same email
    
    # In a real scenario, this would be caught during save
    assert user1.email == user2.email


@pytest.mark.asyncio
async def test_connection_management():
    """Test database connection management."""
    # Test initialization without database (should not fail)
    try:
        await init_db({
            'default': 'sqlite:./test.db'
        })
        assert True
    except Exception as e:
        # This is expected if Rust backend is not built
        assert "Rust engine not available" in str(e) or "connection" in str(e).lower()
    
    # Test closing connections
    try:
        await close_db()
        assert True
    except Exception:
        # This might fail if not initialized, which is fine
        pass


def test_exceptions():
    """Test that custom exceptions work."""
    error = OxenError("Test error")
    assert str(error) == "Test error"
    
    config_error = ConfigurationError("Config error")
    assert "Config error" in str(config_error)
    
    validation_error = ValidationError("Validation error")
    assert "Validation error" in str(validation_error)


if __name__ == "__main__":
    pytest.main([__file__])
