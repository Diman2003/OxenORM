#!/usr/bin/env python3
"""
Basic Migration Test - Testing Working Migration System
"""

import asyncio
import uuid
from datetime import datetime, date, time
from decimal import Decimal

from oxen import connect, disconnect
from oxen.models import Model
from oxen.fields import (
    CharField, TextField, IntField, IntegerField, FloatField, DecimalField,
    BooleanField, DateTimeField, DateField, TimeField, UUIDField, JSONField
)
from oxen.migrations import MigrationEngine
from oxen.exceptions import OperationalError


class SimpleUser(Model):
    """Simple test model with basic field types."""
    username = CharField(max_length=100, unique=True)
    email = CharField(max_length=255, unique=True)
    first_name = CharField(max_length=50)
    last_name = CharField(max_length=50)
    age = IntegerField()
    height = FloatField()
    salary = DecimalField(max_digits=10, decimal_places=2)
    is_active = BooleanField(default=True)
    birth_date = DateField()
    user_id = UUIDField(unique=True)
    profile_data = JSONField(null=True)
    
    class Meta:
        table_name = "simple_users"


class SimpleProduct(Model):
    """Simple test model for products."""
    name = CharField(max_length=200)
    description = TextField()
    price = DecimalField(max_digits=10, decimal_places=2)
    category = CharField(max_length=100)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = "simple_products"


async def test_basic_migration():
    """Test basic migration functionality."""
    print("🚀 Testing Basic Migration System")
    print("=" * 50)
    
    # Test databases
    databases = {
        "SQLite": "sqlite:///test_basic_migration.db",
        "PostgreSQL": "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm",
        "MySQL": "mysql://root:password@localhost:3306/oxenorm"
    }
    
    for db_name, connection_string in databases.items():
        print(f"\n🗄️  Testing {db_name} Basic Migration...")
        
        try:
            # Connect to database
            engine = await connect(connection_string)
            print(f"✅ {db_name} connection successful")
            
            # Create migration engine
            migration_engine = MigrationEngine(engine)
            
            # Generate migration from models
            print("🔄 Generating migration from models...")
            migration = await migration_engine.generate_migration_from_models(
                [SimpleUser, SimpleProduct],
                "Basic migration with simple models",
                "test_runner"
            )
            
            if migration:
                print("✅ Migration generation successful")
                print(f"   Migration ID: {migration.id}")
                print(f"   Migration Name: {migration.name}")
                print(f"   Migration Version: {migration.version}")
                
                # Run migrations
                print("🔄 Running migrations...")
                migration_result = await migration_engine.run_migrations()
                
                if migration_result.get('success'):
                    print("✅ Migrations applied successfully")
                    
                    # Test CRUD operations
                    await test_basic_crud_operations(engine, db_name)
                    
                else:
                    print(f"❌ Migration failed: {migration_result.get('error')}")
            else:
                print("❌ Migration generation failed")
                
        except Exception as e:
            print(f"❌ {db_name} test failed: {str(e)}")
        finally:
            # Cleanup
            try:
                await disconnect(engine)
            except:
                pass


async def test_basic_crud_operations(engine, db_name):
    """Test basic CRUD operations."""
    print(f"🔄 Testing basic CRUD operations for {db_name}...")
    
    # Test User creation
    test_user = SimpleUser(
        username=f"test_user_{uuid.uuid4().hex[:8]}",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        first_name="John",
        last_name="Doe",
        age=30,
        height=175.5,
        salary=Decimal("75000.50"),
        is_active=True,
        birth_date=date(1993, 5, 15),
        user_id=uuid.uuid4(),
        profile_data={
            "skills": ["Python", "JavaScript"],
            "experience": 5
        }
    )
    
    # Save user
    await test_user.save()
    print(f"✅ User created with ID: {test_user.pk}")
    
    # Retrieve user
    retrieved_user = await SimpleUser.get(id=test_user.pk)
    print(f"✅ User retrieved successfully")
    print(f"   username: {retrieved_user.username}")
    print(f"   email: {retrieved_user.email}")
    print(f"   age: {retrieved_user.age}")
    print(f"   salary: {retrieved_user.salary}")
    print(f"   is_active: {retrieved_user.is_active}")
    print(f"   birth_date: {retrieved_user.birth_date}")
    print(f"   user_id: {retrieved_user.user_id}")
    print(f"   profile_data: {retrieved_user.profile_data}")
    
    # Test Product creation
    test_product = SimpleProduct(
        name="Python Programming Book",
        description="Comprehensive guide to Python programming",
        price=Decimal("49.99"),
        category="Books"
    )
    
    await test_product.save()
    print(f"✅ Product created with ID: {test_product.pk}")
    
    # Test queries
    all_users = await SimpleUser.all()
    print(f"✅ Retrieved {len(all_users)} users")
    
    all_products = await SimpleProduct.all()
    print(f"✅ Retrieved {len(all_products)} products")
    
    # Test filtering
    active_users = await SimpleUser.filter(is_active=True)
    print(f"✅ Found {len(active_users)} active users")
    
    # Test counting
    user_count = await SimpleUser.count()
    product_count = await SimpleProduct.count()
    print(f"✅ Total users: {user_count}, Total products: {product_count}")


async def test_migration_status():
    """Test migration status and history."""
    print("\n🔍 Testing Migration Status...")
    
    try:
        # Connect to SQLite for status test
        engine = await connect("sqlite:///test_status.db")
        
        # Create migration engine
        migration_engine = MigrationEngine(engine)
        
        # Generate and run migrations
        migration = await migration_engine.generate_migration_from_models(
            [SimpleUser],
            "Status test migration",
            "test_runner"
        )
        
        result = await migration_engine.run_migrations()
        
        if result.get('success'):
            print("✅ Migrations applied successfully")
            
            # Check migration status
            status = await migration_engine.get_migration_status()
            print(f"✅ Migration status: {status}")
            
            # Get applied migrations
            applied = await migration_engine.get_applied_migrations()
            print(f"✅ Applied migrations: {len(applied)}")
            
            # Get pending migrations
            pending = await migration_engine.get_pending_migrations()
            print(f"✅ Pending migrations: {len(pending)}")
            
        else:
            print(f"❌ Migration failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Status test failed: {str(e)}")
    finally:
        try:
            await disconnect(engine)
        except:
            pass


async def main():
    """Main test function."""
    print("🚀 Basic Migration System Test")
    print("=" * 60)
    
    # Test basic migration
    await test_basic_migration()
    
    # Test migration status
    await test_migration_status()
    
    print("\n" + "=" * 60)
    print("✅ Basic Migration Test Completed!")


if __name__ == "__main__":
    asyncio.run(main()) 