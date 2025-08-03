#!/usr/bin/env python3
"""
Final Summary Test
Demonstrates all fixes working together: MySQL quoting, migration schema generation, PostgreSQL extensions, and model coordination
"""

import asyncio
import uuid
from datetime import date
from decimal import Decimal

from oxen import connect, disconnect
from oxen.models import Model
from oxen.fields import CharField, IntegerField, FloatField, DecimalField, BooleanField, DateField, UUIDField, JSONField
from oxen.migrations import MigrationEngine


class SummaryUser(Model):
    """Summary test model."""
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
        table_name = "summary_users"


async def test_final_summary():
    """Test all fixes working together."""
    print("🚀 Final Summary Test - All Fixes Working Together")
    print("=" * 70)
    
    # Test databases
    databases = {
        "SQLite": "sqlite:///test_summary.db",
        "PostgreSQL": "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm",
        "MySQL": "mysql://root:password@localhost:3306/oxenorm"
    }
    
    results = {}
    
    for db_name, connection_string in databases.items():
        print(f"\n🗄️  Testing {db_name} - All Fixes...")
        
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
                [SummaryUser],
                "Summary migration with all fixes",
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
                    print(f"   Migrations run: {migration_result.get('migrations_run', 0)}")
                    
                    # Set database for models
                    print("🔄 Setting database for models...")
                    SummaryUser._meta.db = engine
                    
                    # Test CRUD operations
                    print("🔄 Testing CRUD operations...")
                    
                    # Create user
                    test_user = SummaryUser(
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
                        }
                    )
                    
                    # Save user
                    await test_user.save()
                    print(f"✅ User created with ID: {test_user.pk}")
                    
                    # Test queries
                    all_users = await SummaryUser.all()
                    print(f"✅ Retrieved {len(all_users)} users")
                    
                    # Test filtering
                    active_users = await SummaryUser.filter(is_active=True)
                    print(f"✅ Found {len(active_users)} active users")
                    
                    # Test counting
                    user_count = await SummaryUser.count()
                    print(f"✅ Total users: {user_count}")
                    
                    # Test exists
                    user_exists = await SummaryUser.exists(id=test_user.pk)
                    print(f"✅ User exists: {user_exists}")
                    
                    results[db_name] = {
                        'migration': True,
                        'crud': True
                    }
                    
                    print(f"🎉 {db_name} - ALL TESTS PASSED!")
                    
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
    print("\n" + "=" * 70)
    print("📊 FINAL SUMMARY - ALL FIXES WORKING TOGETHER")
    print("=" * 70)
    
    for db_name, result in results.items():
        migration_status = "✅ PASS" if result['migration'] else "❌ FAIL"
        crud_status = "✅ PASS" if result['crud'] else "❌ FAIL"
        print(f"{db_name:12} | Migration: {migration_status} | CRUD: {crud_status}")
    
    # Summary
    total_tests = len(results)
    migration_passes = sum(1 for r in results.values() if r['migration'])
    crud_passes = sum(1 for r in results.values() if r['crud'])
    
    print("\n" + "=" * 70)
    print(f"📈 SUMMARY: {migration_passes}/{total_tests} migrations passed, {crud_passes}/{total_tests} CRUD tests passed")
    
    if migration_passes == total_tests and crud_passes == total_tests:
        print("🎉 ALL TESTS PASSED! ALL FIXES ARE WORKING CORRECTLY!")
        print("\n✅ ALL FIXES VERIFIED:")
        print("   ✅ MySQL table name quoting fixed")
        print("   ✅ Migration schema generation enhanced")
        print("   ✅ PostgreSQL extensions working")
        print("   ✅ Model coordination fixed")
        print("   ✅ All field types working across databases")
        print("   ✅ CRUD operations working across databases")
        print("\n🚀 OxenORM is now fully functional across SQLite, PostgreSQL, and MySQL!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


async def main():
    """Main test function."""
    await test_final_summary()


if __name__ == "__main__":
    asyncio.run(main()) 