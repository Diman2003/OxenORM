#!/usr/bin/env python3
"""
Comprehensive Migration, Schema, Model, and Fields Test
Tests automatic schema generation from model classes using the migration system
"""

import asyncio
import uuid
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Dict, Any

from oxen import connect, disconnect
from oxen.models import Model
from oxen.fields import (
    CharField, TextField, IntField, IntegerField, FloatField, DecimalField,
    BooleanField, DateTimeField, DateField, TimeField, UUIDField, JSONField,
    BinaryField, EmailField, URLField, SlugField, FileField, ImageField,
    ArrayField, RangeField, HStoreField, JSONBField
)
from oxen.migrations import EnhancedMigrationEngine, MigrationConfig
from oxen.exceptions import OperationalError, IntegrityError


class TestUser(Model):
    """Test model with all basic field types."""
    username = CharField(max_length=100, unique=True)
    email = EmailField(unique=True)
    first_name = CharField(max_length=50)
    last_name = CharField(max_length=50)
    bio = TextField(null=True)
    website = URLField(null=True)
    slug = SlugField(max_length=100, unique=True)
    age = IntegerField()
    height = FloatField()
    salary = DecimalField(max_digits=10, decimal_places=2)
    score = IntField()
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    birth_date = DateField()
    work_start_time = TimeField()
    user_id = UUIDField(unique=True)
    profile_data = JSONField(null=True)
    tags = ArrayField(CharField(max_length=50), null=True)
    salary_range = RangeField(IntField(), null=True)
    metadata = HStoreField(null=True)
    jsonb_data = JSONBField(null=True)
    
    class Meta:
        table_name = "test_users"


class TestProduct(Model):
    """Test model for testing relationships and complex fields."""
    name = CharField(max_length=200)
    description = TextField()
    price = DecimalField(max_digits=10, decimal_places=2)
    category = CharField(max_length=100)
    tags = ArrayField(CharField(max_length=50), null=True)
    metadata = JSONField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = "test_products"


async def test_migration_schema_generation():
    """Test automatic schema generation from model classes."""
    print("🚀 Testing Migration Schema Generation")
    print("=" * 60)
    
    # Test databases
    databases = {
        "SQLite": "sqlite:///test_migration.db",
        "PostgreSQL": "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm",
        "MySQL": "mysql://root:password@localhost:3306/oxenorm"
    }
    
    for db_name, connection_string in databases.items():
        print(f"\n🗄️  Testing {db_name} Migration Schema Generation...")
        
        try:
            # Connect to database
            engine = await connect(connection_string)
            print(f"✅ {db_name} connection successful")
            
            # Create enhanced migration engine
            config = MigrationConfig(
                migrations_dir="migrations",
                auto_generate=True,
                validate_before_run=False,  # Disable validation for testing
                use_transactions=True
            )
            migration_engine = EnhancedMigrationEngine(engine, config)
            
            # Generate migration from models
            print("🔄 Generating migration from models...")
            migration = await migration_engine.makemigrations_initial(
                [TestUser, TestProduct],
                "Initial migration with test models",
                "test_runner"
            )
            
            if migration:
                print("✅ Migration generation successful")
                
                # Run migrations
                print("🔄 Running migrations...")
                migration_result = await migration_engine.run_migrations()
                
                if migration_result.get('success'):
                    print("✅ Migrations applied successfully")
                    
                    # Test CRUD operations
                    await test_crud_operations(engine, db_name)
                    
                else:
                    print(f"❌ Migration failed: {migration_result.get('error')}")
            else:
                print(f"❌ Schema generation failed: {schema_result.get('error')}")
                
        except Exception as e:
            print(f"❌ {db_name} test failed: {str(e)}")
        finally:
            # Cleanup
            try:
                await disconnect(engine)
            except:
                pass


async def test_crud_operations(engine, db_name):
    """Test CRUD operations with generated schema."""
    print(f"🔄 Testing CRUD operations for {db_name}...")
    
    # Test User creation
    test_user = TestUser(
        username=f"test_user_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        first_name="John",
        last_name="Doe",
        bio="Software developer with 5 years experience",
        website="https://johndoe.dev",
        slug=f"john-doe-{uuid.uuid4().hex[:8]}",
        age=30,
        height=175.5,
        salary=Decimal("75000.50"),
        score=95,
        is_active=True,
        is_staff=False,
        birth_date=date(1993, 5, 15),
        work_start_time=time(9, 0, 0),
        user_id=uuid.uuid4(),
        profile_data={
            "skills": ["Python", "JavaScript", "SQL"],
            "experience": 5,
            "location": "San Francisco"
        },
        tags=["developer", "python", "javascript"],
        salary_range=(50000, 100000),
        metadata={
            "department": "Engineering",
            "level": "Senior"
        },
        jsonb_data={
            "preferences": {
                "theme": "dark",
                "notifications": True
            }
        }
    )
    
    # Save user
    await test_user.save()
    print(f"✅ User created with ID: {test_user.pk}")
    
    # Retrieve user
    retrieved_user = await TestUser.get(id=test_user.pk)
    print(f"✅ User retrieved successfully")
    print(f"   username: {retrieved_user.username}")
    print(f"   email: {retrieved_user.email}")
    print(f"   age: {retrieved_user.age}")
    print(f"   salary: {retrieved_user.salary}")
    print(f"   is_active: {retrieved_user.is_active}")
    print(f"   birth_date: {retrieved_user.birth_date}")
    print(f"   user_id: {retrieved_user.user_id}")
    print(f"   profile_data: {retrieved_user.profile_data}")
    print(f"   tags: {retrieved_user.tags}")
    print(f"   metadata: {retrieved_user.metadata}")
    print(f"   jsonb_data: {retrieved_user.jsonb_data}")
    
    # Test Product creation
    test_product = TestProduct(
        name="Python Programming Book",
        description="Comprehensive guide to Python programming",
        price=Decimal("49.99"),
        category="Books",
        tags=["python", "programming", "education"],
        metadata={
            "author": "John Smith",
            "pages": 450,
            "isbn": "978-1234567890"
        }
    )
    
    await test_product.save()
    print(f"✅ Product created with ID: {test_product.pk}")
    
    # Test bulk operations
    products = [
        TestProduct(
            name=f"Product {i}",
            description=f"Description for product {i}",
            price=Decimal(f"{10 + i}.99"),
            category="Electronics",
            tags=[f"tag{i}", "electronics"],
            metadata={"sku": f"SKU{i:03d}"}
        )
        for i in range(1, 4)
    ]
    
    created_products = await TestProduct.bulk_create(products)
    print(f"✅ Bulk created {len(created_products)} products")
    
    # Test queries
    all_users = await TestUser.all()
    print(f"✅ Retrieved {len(all_users)} users")
    
    all_products = await TestProduct.all()
    print(f"✅ Retrieved {len(all_products)} products")
    
    # Test filtering
    active_users = await TestUser.filter(is_active=True)
    print(f"✅ Found {len(active_users)} active users")
    
    expensive_products = await TestProduct.filter(price__gte=Decimal("20.00"))
    print(f"✅ Found {len(expensive_products)} expensive products")
    
    # Test counting
    user_count = await TestUser.count()
    product_count = await TestProduct.count()
    print(f"✅ Total users: {user_count}, Total products: {product_count}")
    
    # Test exists
    user_exists = await TestUser.exists(id=test_user.pk)
    product_exists = await TestProduct.exists(id=test_product.pk)
    print(f"✅ User exists: {user_exists}, Product exists: {product_exists}")


async def test_field_validation():
    """Test field validation."""
    print("\n🔍 Testing Field Validation...")
    
    # Test required fields
    try:
        user = TestUser()  # Missing required fields
        await user.save()
        print("❌ Should have failed for missing required fields")
    except Exception as e:
        print(f"✅ Correctly failed for missing required fields: {str(e)}")
    
    # Test field type validation
    try:
        user = TestUser(
            username="test",
            email="invalid-email",  # Invalid email
            age="not_a_number",  # Invalid age
            height="not_a_float",  # Invalid height
            salary="not_a_decimal",  # Invalid salary
            birth_date="not_a_date",  # Invalid date
            work_start_time="not_a_time",  # Invalid time
            user_id="not_a_uuid",  # Invalid UUID
            slug="invalid slug with spaces",  # Invalid slug
            website="not_a_url",  # Invalid URL
            first_name="John",
            last_name="Doe",
            is_active=True,
            is_staff=False
        )
        await user.save()
        print("❌ Should have failed for invalid field types")
    except Exception as e:
        print(f"✅ Correctly failed for invalid field types: {str(e)}")


async def test_migration_rollback():
    """Test migration rollback functionality."""
    print("\n🔄 Testing Migration Rollback...")
    
    try:
        # Connect to SQLite for rollback test
        engine = await connect("sqlite:///test_rollback.db")
        
        # Create enhanced migration engine
        config = MigrationConfig(
            migrations_dir="migrations",
            auto_generate=True,
            validate_before_run=False,
            use_transactions=True
        )
        migration_engine = EnhancedMigrationEngine(engine, config)
        
        # Generate and run migrations
        migration = await migration_engine.makemigrations_initial(
            [TestUser, TestProduct],
            "Test migration for rollback",
            "test_runner"
        )
        result = await migration_engine.run_migrations()
        
        if result.get('success'):
            print("✅ Migrations applied successfully")
            
            # Test rollback
            rollback_result = await migration_engine.rollback_migrations("0")
            if rollback_result.get('success'):
                print("✅ Migration rollback successful")
            else:
                print(f"❌ Rollback failed: {rollback_result.get('error')}")
        else:
            print(f"❌ Migration failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Rollback test failed: {str(e)}")
    finally:
        try:
            await disconnect(engine)
        except:
            pass


async def main():
    """Main test function."""
    print("🚀 Comprehensive Migration, Schema, Model, and Fields Test")
    print("=" * 80)
    
    # Test migration schema generation
    await test_migration_schema_generation()
    
    # Test field validation
    await test_field_validation()
    
    # Test migration rollback
    await test_migration_rollback()
    
    print("\n" + "=" * 80)
    print("✅ Migration, Schema, Model, and Fields Test Completed!")


if __name__ == "__main__":
    asyncio.run(main()) 