#!/usr/bin/env python3
"""
Comprehensive Fixes Test
Tests all the fixes: MySQL quoting, migration schema generation, PostgreSQL extensions
"""

import asyncio
import uuid
from datetime import datetime, date, time
from decimal import Decimal

from oxen import connect, disconnect
from oxen.models import Model
from oxen.fields import (
    CharField, TextField, IntField, IntegerField, FloatField, DecimalField,
    BooleanField, DateTimeField, DateField, TimeField, UUIDField, JSONField,
    HStoreField, JSONBField
)
from oxen.migrations import MigrationEngine
from oxen.exceptions import OperationalError


class ComprehensiveUser(Model):
    """Comprehensive test model with all field types."""
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
    metadata = HStoreField(null=True)
    jsonb_data = JSONBField(null=True)
    
    class Meta:
        table_name = "comprehensive_users"


class ComprehensiveProduct(Model):
    """Comprehensive test model for products."""
    name = CharField(max_length=200)
    description = TextField()
    price = DecimalField(max_digits=10, decimal_places=2)
    category = CharField(max_length=100)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = "comprehensive_products"


async def test_comprehensive_fixes():
    """Test all the fixes comprehensively."""
    print("🚀 Comprehensive Fixes Test")
    print("=" * 60)
    
    # Test databases
    databases = {
        "SQLite": "sqlite:///test_comprehensive.db",
        "PostgreSQL": "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm",
        "MySQL": "mysql://root:password@localhost:3306/oxenorm"
    }
    
    results = {}
    
    for db_name, connection_string in databases.items():
        print(f"\n🗄️  Testing {db_name} Comprehensive Fixes...")
        
        try:
            # Connect to database
            engine = await connect(connection_string)
            print(f"✅ {db_name} connection successful")
            
            # Enable PostgreSQL extensions if needed
            if 'postgresql' in connection_string.lower():
                print("🔄 Enabling PostgreSQL extensions...")
                await engine.execute_query("CREATE EXTENSION IF NOT EXISTS hstore")
                print("✅ hstore extension enabled")
            
            # Create migration engine
            migration_engine = MigrationEngine(engine)
            
            # Generate migration from models
            print("🔄 Generating migration from models...")
            migration = await migration_engine.generate_migration_from_models(
                [ComprehensiveUser, ComprehensiveProduct],
                "Comprehensive migration with all field types",
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
                    crud_success = await test_comprehensive_crud_operations(engine, db_name)
                    results[db_name] = {
                        'migration': True,
                        'crud': crud_success
                    }
                    
                else:
                    print(f"❌ Migration failed: {migration_result.get('error')}")
                    results[db_name] = {
                        'migration': False,
                        'crud': False
                    }
            else:
                print("❌ Migration generation failed")
                results[db_name] = {
                    'migration': False,
                    'crud': False
                }
                
        except Exception as e:
            print(f"❌ {db_name} test failed: {str(e)}")
            results[db_name] = {
                'migration': False,
                'crud': False
            }
        finally:
            # Cleanup
            try:
                await disconnect(engine)
            except:
                pass
    
    # Print comprehensive results
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    for db_name, result in results.items():
        migration_status = "✅ PASS" if result['migration'] else "❌ FAIL"
        crud_status = "✅ PASS" if result['crud'] else "❌ FAIL"
        print(f"{db_name:12} | Migration: {migration_status} | CRUD: {crud_status}")
    
    # Summary
    total_tests = len(results)
    migration_passes = sum(1 for r in results.values() if r['migration'])
    crud_passes = sum(1 for r in results.values() if r['crud'])
    
    print("\n" + "=" * 60)
    print(f"📈 SUMMARY: {migration_passes}/{total_tests} migrations passed, {crud_passes}/{total_tests} CRUD tests passed")
    
    if migration_passes == total_tests and crud_passes == total_tests:
        print("🎉 ALL TESTS PASSED! All fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


async def test_comprehensive_crud_operations(engine, db_name):
    """Test comprehensive CRUD operations."""
    print(f"🔄 Testing comprehensive CRUD operations for {db_name}...")
    
    try:
        # Test User creation
        test_user = ComprehensiveUser(
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
                "skills": ["Python", "JavaScript", "SQL"],
                "experience": 5,
                "location": "San Francisco"
            },
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
        retrieved_user = await ComprehensiveUser.get(id=test_user.pk)
        print(f"✅ User retrieved successfully")
        print(f"   username: {retrieved_user.username}")
        print(f"   email: {retrieved_user.email}")
        print(f"   age: {retrieved_user.age}")
        print(f"   salary: {retrieved_user.salary}")
        print(f"   is_active: {retrieved_user.is_active}")
        print(f"   birth_date: {retrieved_user.birth_date}")
        print(f"   user_id: {retrieved_user.user_id}")
        print(f"   profile_data: {retrieved_user.profile_data}")
        print(f"   metadata: {retrieved_user.metadata}")
        print(f"   jsonb_data: {retrieved_user.jsonb_data}")
        
        # Test Product creation
        test_product = ComprehensiveProduct(
            name="Python Programming Book",
            description="Comprehensive guide to Python programming",
            price=Decimal("49.99"),
            category="Books"
        )
        
        await test_product.save()
        print(f"✅ Product created with ID: {test_product.pk}")
        
        # Test queries
        all_users = await ComprehensiveUser.all()
        print(f"✅ Retrieved {len(all_users)} users")
        
        all_products = await ComprehensiveProduct.all()
        print(f"✅ Retrieved {len(all_products)} products")
        
        # Test filtering
        active_users = await ComprehensiveUser.filter(is_active=True)
        print(f"✅ Found {len(active_users)} active users")
        
        # Test counting
        user_count = await ComprehensiveUser.count()
        product_count = await ComprehensiveProduct.count()
        print(f"✅ Total users: {user_count}, Total products: {product_count}")
        
        # Test exists
        user_exists = await ComprehensiveUser.exists(id=test_user.pk)
        product_exists = await ComprehensiveProduct.exists(id=test_product.pk)
        print(f"✅ User exists: {user_exists}, Product exists: {product_exists}")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations failed: {str(e)}")
        return False


async def main():
    """Main test function."""
    print("🚀 Comprehensive Fixes Test")
    print("=" * 80)
    
    # Test comprehensive fixes
    await test_comprehensive_fixes()
    
    print("\n" + "=" * 80)
    print("✅ Comprehensive Fixes Test Completed!")


if __name__ == "__main__":
    asyncio.run(main()) 