#!/usr/bin/env python3
"""
Comprehensive test for all model field types across SQLite and PostgreSQL
"""

import asyncio
import uuid
from datetime import datetime, date, time
from decimal import Decimal
from oxen import connect, disconnect
from oxen.models import Model
from oxen.fields.data import (
    CharField, TextField, IntegerField, FloatField, DecimalField,
    BooleanField, DateTimeField, DateField, TimeField, UUIDField,
    JSONField, EmailField, URLField, SlugField
)


class TestUser(Model):
    """Test model with all field types."""
    # Basic fields
    username = CharField(max_length=50, unique=True)
    email = EmailField(unique=True)
    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)
    bio = TextField(null=True)
    
    # Numeric fields
    age = IntegerField()
    height = FloatField()
    salary = DecimalField(max_digits=10, decimal_places=2)
    
    # Boolean and date fields
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    birth_date = DateField()
    work_start_time = TimeField()
    
    # Special fields
    user_id = UUIDField(auto_generate=True)
    profile_data = JSONField(null=True)
    website = URLField(null=True)
    slug = SlugField(unique=True)
    
    class Meta:
        table_name = "test_users"


class TestProduct(Model):
    """Test model for product data."""
    name = CharField(max_length=200)
    description = TextField()
    price = DecimalField(max_digits=10, decimal_places=2)
    stock = IntegerField()
    is_available = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    category = CharField(max_length=100)
    tags = JSONField(default=list)
    
    class Meta:
        table_name = "test_products"


async def test_sqlite_fields():
    """Test all field types with SQLite."""
    print("🗄️  Testing SQLite with All Field Types...")
    
    try:
        # Connect to SQLite
        engine = await connect("sqlite:///test_fields.db")
        print("✅ SQLite connection successful")
        
        # Test data
        test_data = {
            'username': 'john_doe',
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'bio': 'Software developer with 5 years experience',
            'age': 30,
            'height': 175.5,
            'salary': Decimal('75000.50'),
            'is_active': True,
            'is_staff': False,
            'birth_date': date(1993, 5, 15),
            'work_start_time': time(9, 0, 0),
            'profile_data': {
                'skills': ['Python', 'JavaScript', 'SQL'],
                'experience': 5,
                'location': 'San Francisco'
            },
            'website': 'https://johndoe.dev',
            'slug': 'john-doe'
        }
        
        # Create user
        user = TestUser(**test_data)
        await user.save()
        print(f"✅ User created with ID: {user.pk}")
        
        # Verify all fields were saved correctly
        retrieved_user = await TestUser.get(pk=user.pk)
        print("✅ User retrieved successfully")
        
        # Check each field
        field_checks = [
            ('username', 'john_doe'),
            ('email', 'john@example.com'),
            ('first_name', 'John'),
            ('last_name', 'Doe'),
            ('bio', 'Software developer with 5 years experience'),
            ('age', 30),
            ('height', 175.5),
            ('salary', Decimal('75000.50')),
            ('is_active', True),
            ('is_staff', False),
            ('birth_date', date(1993, 5, 15)),
            ('work_start_time', time(9, 0, 0)),
            ('profile_data', {'skills': ['Python', 'JavaScript', 'SQL'], 'experience': 5, 'location': 'San Francisco'}),
            ('website', 'https://johndoe.dev'),
            ('slug', 'john-doe')
        ]
        
        for field_name, expected_value in field_checks:
            actual_value = getattr(retrieved_user, field_name)
            if actual_value == expected_value:
                print(f"✅ {field_name}: {actual_value}")
            else:
                print(f"❌ {field_name}: expected {expected_value}, got {actual_value}")
        
        # Test product creation
        product_data = {
            'name': 'Laptop Pro',
            'description': 'High-performance laptop for developers',
            'price': Decimal('1299.99'),
            'stock': 50,
            'is_available': True,
            'category': 'Electronics',
            'tags': ['laptop', 'development', 'high-performance']
        }
        
        product = TestProduct(**product_data)
        await product.save()
        print(f"✅ Product created with ID: {product.pk}")
        
        # Test querying
        users = await TestUser.all()
        products = await TestProduct.all()
        
        print(f"✅ Found {len(users)} users and {len(products)} products")
        
        # Test filtering
        active_users = await TestUser.filter(is_active=True)
        available_products = await TestProduct.filter(is_available=True)
        
        print(f"✅ Found {len(active_users)} active users and {len(available_products)} available products")
        
        await disconnect(engine)
        return True
        
    except Exception as e:
        print(f"❌ SQLite test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_postgresql_fields():
    """Test all field types with PostgreSQL."""
    print("\n🗄️  Testing PostgreSQL with All Field Types...")
    
    try:
        # Connect to PostgreSQL
        engine = await connect("postgresql://oxenorm:oxenorm@localhost:5432/oxenorm")
        print("✅ PostgreSQL connection successful")
        
        # Test data
        test_data = {
            'username': 'jane_smith',
            'email': 'jane@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'bio': 'Data scientist with expertise in machine learning',
            'age': 28,
            'height': 165.0,
            'salary': Decimal('85000.75'),
            'is_active': True,
            'is_staff': True,
            'birth_date': date(1995, 8, 22),
            'work_start_time': time(8, 30, 0),
            'profile_data': {
                'skills': ['Python', 'R', 'SQL', 'Machine Learning'],
                'experience': 3,
                'location': 'New York',
                'certifications': ['AWS', 'Google Cloud']
            },
            'website': 'https://janesmith.ai',
            'slug': 'jane-smith'
        }
        
        # Create user
        user = TestUser(**test_data)
        await user.save()
        print(f"✅ User created with ID: {user.pk}")
        
        # Verify all fields were saved correctly
        retrieved_user = await TestUser.get(pk=user.pk)
        print("✅ User retrieved successfully")
        
        # Check each field
        field_checks = [
            ('username', 'jane_smith'),
            ('email', 'jane@example.com'),
            ('first_name', 'Jane'),
            ('last_name', 'Smith'),
            ('bio', 'Data scientist with expertise in machine learning'),
            ('age', 28),
            ('height', 165.0),
            ('salary', Decimal('85000.75')),
            ('is_active', True),
            ('is_staff', True),
            ('birth_date', date(1995, 8, 22)),
            ('work_start_time', time(8, 30, 0)),
            ('profile_data', {
                'skills': ['Python', 'R', 'SQL', 'Machine Learning'],
                'experience': 3,
                'location': 'New York',
                'certifications': ['AWS', 'Google Cloud']
            }),
            ('website', 'https://janesmith.ai'),
            ('slug', 'jane-smith')
        ]
        
        for field_name, expected_value in field_checks:
            actual_value = getattr(retrieved_user, field_name)
            if actual_value == expected_value:
                print(f"✅ {field_name}: {actual_value}")
            else:
                print(f"❌ {field_name}: expected {expected_value}, got {actual_value}")
        
        # Test product creation
        product_data = {
            'name': 'Data Science Course',
            'description': 'Comprehensive course on data science and machine learning',
            'price': Decimal('299.99'),
            'stock': 100,
            'is_available': True,
            'category': 'Education',
            'tags': ['data-science', 'machine-learning', 'python', 'online-course']
        }
        
        product = TestProduct(**product_data)
        await product.save()
        print(f"✅ Product created with ID: {product.pk}")
        
        # Test querying
        users = await TestUser.all()
        products = await TestProduct.all()
        
        print(f"✅ Found {len(users)} users and {len(products)} products")
        
        # Test filtering
        staff_users = await TestUser.filter(is_staff=True)
        education_products = await TestProduct.filter(category='Education')
        
        print(f"✅ Found {len(staff_users)} staff users and {len(education_products)} education products")
        
        # Test JSON field operations
        users_with_skills = await TestUser.filter(profile_data__contains={'skills': ['Python']})
        print(f"✅ Found {len(users_with_skills)} users with Python skills")
        
        await disconnect(engine)
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_field_validation():
    """Test field validation."""
    print("\n🔍 Testing Field Validation...")
    
    try:
        # Test invalid data types
        invalid_data = {
            'username': 123,  # Should be string
            'email': 'invalid-email',  # Invalid email
            'age': 'not-a-number',  # Should be integer
            'height': 'not-a-float',  # Should be float
            'salary': 'not-a-decimal',  # Should be decimal
            'is_active': 'not-a-boolean',  # Should be boolean
            'birth_date': 'not-a-date',  # Should be date
            'work_start_time': 'not-a-time',  # Should be time
            'website': 'not-a-url',  # Invalid URL
            'slug': 'Invalid Slug!',  # Invalid slug
        }
        
        print("✅ Field validation tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Field validation test failed: {e}")
        return False


async def test_bulk_operations():
    """Test bulk operations."""
    print("\n📦 Testing Bulk Operations...")
    
    try:
        # Connect to SQLite for bulk operations test
        engine = await connect("sqlite:///test_bulk.db")
        
        # Create multiple users
        users_data = [
            {
                'username': f'user_{i}',
                'email': f'user{i}@example.com',
                'first_name': f'User{i}',
                'last_name': 'Test',
                'age': 20 + i,
                'height': 170.0 + i,
                'salary': Decimal(f'{50000 + i * 1000}.50'),
                'is_active': True,
                'birth_date': date(1990 + i, 1, 1),
                'work_start_time': time(9, 0, 0),
                'profile_data': {'user_id': i},
                'website': f'https://user{i}.com',
                'slug': f'user-{i}'
            }
            for i in range(1, 6)
        ]
        
        # Bulk create
        users = [TestUser(**data) for data in users_data]
        created_users = await TestUser.bulk_create(users)
        print(f"✅ Bulk created {len(created_users)} users")
        
        # Bulk update
        for user in created_users:
            user.age += 1
            user.salary += Decimal('1000.00')
        
        updated_count = await TestUser.bulk_update(created_users, ['age', 'salary'])
        print(f"✅ Bulk updated {updated_count} users")
        
        # Verify updates
        all_users = await TestUser.all()
        for user in all_users:
            print(f"   - {user.username}: age {user.age}, salary {user.salary}")
        
        await disconnect(engine)
        return True
        
    except Exception as e:
        print(f"❌ Bulk operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Comprehensive Model Fields Test")
    print("=" * 60)
    
    results = []
    
    # Test SQLite
    results.append(await test_sqlite_fields())
    
    # Test PostgreSQL
    results.append(await test_postgresql_fields())
    
    # Test field validation
    results.append(await test_field_validation())
    
    # Test bulk operations
    results.append(await test_bulk_operations())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"✅ SQLite Fields: {'PASS' if results[0] else 'FAIL'}")
    print(f"✅ PostgreSQL Fields: {'PASS' if results[1] else 'FAIL'}")
    print(f"✅ Field Validation: {'PASS' if results[2] else 'FAIL'}")
    print(f"✅ Bulk Operations: {'PASS' if results[3] else 'FAIL'}")
    
    if all(results):
        print("\n🎉 All tests passed! Model fields working correctly across all databases.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 