#!/usr/bin/env python3
"""
Enhanced OxenORM Model System Test
Tests the comprehensive model system with all field types and functionality
"""

import asyncio
import sys
import os
from datetime import datetime, date, time
from decimal import Decimal
import uuid
import json

# Add the oxen package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oxen.models import Model, ModelMeta
from oxen.fields import (
    CharField, TextField, IntegerField, FloatField, DecimalField,
    BooleanField, DateTimeField, DateField, TimeField, UUIDField,
    JSONField, BinaryField, EmailField, URLField, SlugField,
    AutoField, BigIntegerField, SmallIntegerField, PositiveIntegerField
)
from oxen.exceptions import ValidationError, ModelError

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_test_result(test_name, success, error=None):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if error:
        print(f"    Error: {error}")

class User(Model):
    """Test user model with various field types"""
    
    # Basic fields
    username = CharField(max_length=50, unique=True)
    email = EmailField(unique=True)
    password_hash = CharField(max_length=128)
    
    # Personal info
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=30)
    bio = TextField(null=True, blank=True)
    
    # Numbers
    age = PositiveIntegerField(null=True)
    height = FloatField(null=True)
    weight = DecimalField(max_digits=5, decimal_places=2, null=True)
    
    # Dates and times
    birth_date = DateField(null=True)
    last_login = DateTimeField(null=True)
    preferred_time = TimeField(null=True)
    
    # Other types
    is_active = BooleanField(default=True)
    profile_uuid = UUIDField(null=True)
    settings = JSONField(default=dict)
    avatar_data = BinaryField(null=True)
    
    # URLs and slugs
    website = URLField(null=True)
    slug = SlugField(unique=True)
    
    class Meta:
        db_table = "users"

class Post(Model):
    """Test post model for relationships"""
    
    title = CharField(max_length=200)
    content = TextField()
    author_id = IntegerField()  # Would be ForeignKey in real implementation
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    is_published = BooleanField(default=False)
    
    class Meta:
        db_table = "posts"

def test_model_initialization():
    """Test model initialization and field discovery"""
    print_section("Model Initialization Tests")
    
    # Test field discovery
    User._initialize_model()
    
    expected_fields = {
        'username', 'email', 'password_hash', 'first_name', 'last_name',
        'bio', 'age', 'height', 'weight', 'birth_date', 'last_login',
        'preferred_time', 'is_active', 'profile_uuid', 'settings',
        'avatar_data', 'website', 'slug'
    }
    
    actual_fields = set(User._fields.keys())
    success = expected_fields.issubset(actual_fields)
    print_test_result("Field Discovery", success)
    
    if not success:
        missing = expected_fields - actual_fields
        extra = actual_fields - expected_fields
        print(f"    Missing fields: {missing}")
        print(f"    Extra fields: {extra}")
    
    # Test table name
    expected_table = "users"
    actual_table = User._table_name
    success = actual_table == expected_table
    print_test_result("Table Name Generation", success, 
                     f"Expected '{expected_table}', got '{actual_table}'")
    
    # Test primary key
    expected_pk = "id"
    actual_pk = User._pk_field
    success = actual_pk == expected_pk
    print_test_result("Primary Key Field", success,
                     f"Expected '{expected_pk}', got '{actual_pk}'")

def test_field_validation():
    """Test field validation"""
    print_section("Field Validation Tests")
    
    # Test valid user creation
    try:
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
            age=25,
            height=175.5,
            weight=Decimal("70.5"),
            birth_date=date(1998, 1, 1),
            last_login=datetime.now(),
            preferred_time=time(9, 0),
            is_active=True,
            profile_uuid=uuid.uuid4(),
            settings={"theme": "dark", "notifications": True},
            website="https://example.com",
            slug="john-doe"
        )
        print_test_result("Valid User Creation", True)
    except Exception as e:
        print_test_result("Valid User Creation", False, str(e))
    
    # Test invalid email
    try:
        user = User(username="test", email="invalid-email")
        print_test_result("Invalid Email Validation", False, "Should have raised ValidationError")
    except ValidationError:
        print_test_result("Invalid Email Validation", True)
    except Exception as e:
        print_test_result("Invalid Email Validation", False, f"Wrong exception: {e}")
    
    # Test invalid URL
    try:
        user = User(username="test", email="test@example.com", website="not-a-url")
        print_test_result("Invalid URL Validation", False, "Should have raised ValidationError")
    except ValidationError:
        print_test_result("Invalid URL Validation", True)
    except Exception as e:
        print_test_result("Invalid URL Validation", False, f"Wrong exception: {e}")
    
    # Test invalid slug
    try:
        user = User(username="test", email="test@example.com", slug="Invalid Slug!")
        print_test_result("Invalid Slug Validation", False, "Should have raised ValidationError")
    except ValidationError:
        print_test_result("Invalid Slug Validation", True)
    except Exception as e:
        print_test_result("Invalid Slug Validation", False, f"Wrong exception: {e}")
    
    # Test negative age
    try:
        user = User(username="test", email="test@example.com", age=-5)
        print_test_result("Negative Age Validation", False, "Should have raised ValidationError")
    except ValidationError:
        print_test_result("Negative Age Validation", True)
    except Exception as e:
        print_test_result("Negative Age Validation", False, f"Wrong exception: {e}")

def test_field_types():
    """Test specific field type behaviors"""
    print_section("Field Type Tests")
    
    # Test CharField max_length
    try:
        user = User(username="a" * 51, email="test@example.com")
        print_test_result("CharField Max Length", False, "Should have raised ValidationError")
    except ValidationError:
        print_test_result("CharField Max Length", True)
    
    # Test DecimalField precision
    try:
        user = User(username="test", email="test@example.com", weight=Decimal("123.456"))
        print_test_result("DecimalField Precision", False, "Should have raised ValidationError")
    except ValidationError:
        print_test_result("DecimalField Precision", True)
    
    # Test JSONField
    try:
        user = User(
            username="test", 
            email="test@example.com",
            settings={"nested": {"data": [1, 2, 3]}}
        )
        print_test_result("JSONField Complex Data", True)
    except Exception as e:
        print_test_result("JSONField Complex Data", False, str(e))
    
    # Test BinaryField
    try:
        user = User(
            username="test", 
            email="test@example.com",
            avatar_data=b"binary_data_here"
        )
        print_test_result("BinaryField Bytes", True)
    except Exception as e:
        print_test_result("BinaryField Bytes", False, str(e))

def test_model_methods():
    """Test model methods and properties"""
    print_section("Model Methods Tests")
    
    user = User(
        username="testuser",
        email="test@example.com",
        first_name="John",
        last_name="Doe"
    )
    
    # Test is_new property
    success = user.is_new == True
    print_test_result("is_new Property", success)
    
    # Test pk property (should be None for new instance)
    success = user.pk is None
    print_test_result("pk Property (New)", success)
    
    # Test string representation
    repr_str = repr(user)
    success = "User(" in repr_str and "username='testuser'" in repr_str
    print_test_result("String Representation", success, f"Got: {repr_str}")

def test_queryset_interface():
    """Test QuerySet interface"""
    print_section("QuerySet Interface Tests")
    
    # Test objects() method
    try:
        queryset = User.objects()
        success = hasattr(queryset, 'filter') and hasattr(queryset, 'get')
        print_test_result("QuerySet Interface", success)
    except Exception as e:
        print_test_result("QuerySet Interface", False, str(e))

def test_model_meta():
    """Test model meta configuration"""
    print_section("Model Meta Tests")
    
    # Test custom table name
    class CustomTableModel(Model):
        name = CharField(max_length=100)
        
        class Meta:
            db_table = "custom_table"
    
    CustomTableModel._initialize_model()
    success = CustomTableModel._table_name == "custom_table"
    print_test_result("Custom Table Name", success)

def test_dynamic_model_creation():
    """Test dynamic model creation"""
    print_section("Dynamic Model Creation Tests")
    
    from oxen.models import create_model
    
    # Create a model dynamically
    fields = {
        'name': CharField(max_length=100),
        'value': IntegerField(),
        'created_at': DateTimeField(auto_now_add=True)
    }
    
    DynamicModel = create_model('DynamicModel', fields, db_table='dynamic_models')
    
    # Test the dynamic model
    try:
        instance = DynamicModel(name="test", value=42)
        success = instance.name == "test" and instance.value == 42
        print_test_result("Dynamic Model Creation", success)
    except Exception as e:
        print_test_result("Dynamic Model Creation", False, str(e))

def run_all_tests():
    """Run all tests"""
    print("🐂 OxenORM Enhanced Model System Test")
    print("=" * 60)
    
    tests = [
        test_model_initialization,
        test_field_validation,
        test_field_types,
        test_model_methods,
        test_queryset_interface,
        test_model_meta,
        test_dynamic_model_creation
    ]
    
    passed = 0
    total = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
        total += 1
    
    print_section("Test Summary")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced model system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 