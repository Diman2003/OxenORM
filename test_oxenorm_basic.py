#!/usr/bin/env python3
"""
Basic test script for OxenORM Python components

This script tests the basic structure and imports without requiring the Rust backend.
"""

import sys
import os

# Add the oxen package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'oxen'))

def test_imports():
    """Test that all modules can be imported correctly."""
    print("Testing imports...")
    
    try:
        from oxen import Model, init_db, close_db
        print("✓ Core imports successful")
    except ImportError as e:
        print(f"✗ Core imports failed: {e}")
        return False
    
    try:
        from oxen.fields import (
            IntField, CharField, TextField, BooleanField, DateTimeField,
            DateField, TimeField, DecimalField, FloatField, JSONField, UUIDField
        )
        print("✓ Field imports successful")
    except ImportError as e:
        print(f"✗ Field imports failed: {e}")
        return False
    
    try:
        from oxen.queryset import QuerySet, Q
        print("✓ QuerySet imports successful")
    except ImportError as e:
        print(f"✗ QuerySet imports failed: {e}")
        return False
    
    try:
        from oxen.exceptions import (
            OxenError, ConfigurationError, ValidationError, IntegrityError,
            DoesNotExist, MultipleObjectsReturned, OperationalError
        )
        print("✓ Exception imports successful")
    except ImportError as e:
        print(f"✗ Exception imports failed: {e}")
        return False
    
    return True


def test_model_definition():
    """Test that models can be defined correctly."""
    print("\nTesting model definition...")
    
    try:
        from oxen import Model
        from oxen.fields import IntField, CharField, BooleanField, DateTimeField
        
        class TestUser(Model):
            id = IntField(primary_key=True)
            username = CharField(max_length=50, unique=True)
            email = CharField(max_length=100, unique=True)
            is_active = BooleanField(default=True)
            created_at = DateTimeField(auto_now_add=True)
            
            class Meta:
                table = "test_users"
        
        print("✓ Model definition successful")
        print(f"  - Model name: {TestUser.__name__}")
        print(f"  - Table name: {TestUser.Meta.table}")
        print(f"  - PK field: id")  # Default PK field
        
        return True
    except Exception as e:
        print(f"✗ Model definition failed: {e}")
        return False


def test_field_validation():
    """Test field validation."""
    print("\nTesting field validation...")
    
    try:
        from oxen.fields import IntField, CharField, BooleanField
        
        # Test IntField
        int_field = IntField()
        assert int_field.validate(42) == 42
        assert int_field.validate("42") == 42
        
        # Test CharField
        char_field = CharField(max_length=10)
        assert char_field.validate("hello") == "hello"
        
        # Test BooleanField
        bool_field = BooleanField()
        assert bool_field.validate(True) is True
        assert bool_field.validate("true") is True
        assert bool_field.validate("false") is False
        
        print("✓ Field validation successful")
        return True
    except Exception as e:
        print(f"✗ Field validation failed: {e}")
        return False


def test_queryset_building():
    """Test QuerySet building."""
    print("\nTesting QuerySet building...")
    
    try:
        from oxen.queryset import QuerySet, Q
        from oxen import Model
        from oxen.fields import IntField, CharField
        
        class TestModel(Model):
            id = IntField(primary_key=True)
            name = CharField(max_length=100)
            
            class Meta:
                table = "test_table"
        
        # Test Q objects
        q1 = Q(name="test")
        q2 = Q(id=1)
        q3 = q1 & q2
        
        assert q1.to_dict() == {"name": "test"}
        assert q3.to_dict() == {"name": "test", "id": 1}
        
        # Test QuerySet
        qs = QuerySet(TestModel)
        qs = qs.filter(name="test").limit(10).order_by("id")
        
        assert qs._conditions == {"name": "test"}
        assert qs._limit == 10
        assert qs._order_by == ["id"]
        
        print("✓ QuerySet building successful")
        return True
    except Exception as e:
        print(f"✗ QuerySet building failed: {e}")
        return False


def test_exceptions():
    """Test exception classes."""
    print("\nTesting exceptions...")
    
    try:
        from oxen.exceptions import (
            OxenError, ValidationError, DoesNotExist, MultipleObjectsReturned
        )
        
        # Test base exception
        error = OxenError("Test error")
        assert str(error) == "Test error"
        
        # Test validation error
        val_error = ValidationError("Invalid value", field="name", value="test")
        assert val_error.field == "name"
        assert val_error.value == "test"
        
        # Test other exceptions
        DoesNotExist("Object not found")
        MultipleObjectsReturned("Multiple objects found")
        
        print("✓ Exceptions successful")
        return True
    except Exception as e:
        print(f"✗ Exceptions failed: {e}")
        return False


def main():
    """Run all tests."""
    print("OxenORM Python Components Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_model_definition,
        test_field_validation,
        test_queryset_building,
        test_exceptions,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Python structure is working correctly.")
        print("\nNext steps:")
        print("1. Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
        print("2. Build the Rust backend: cargo build")
        print("3. Run integration tests: python -m pytest tests/")
        print("4. Run performance benchmarks: python -m pytest tests/benchmarks/")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 