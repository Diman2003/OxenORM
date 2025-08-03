#!/usr/bin/env python3
"""
QuerySet Debug Test
Debug QuerySet issues and identify specific problems
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import oxen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from oxen import connect, disconnect
from oxen.models import Model, set_database_for_models
from oxen.fields import CharField, IntegerField, BooleanField, DateField
from oxen.migrations import MigrationEngine
from oxen.expressions import Q


class QueryTestUser(Model):
    """Test model for QuerySet debugging."""
    name = CharField(max_length=100)
    age = IntegerField()
    is_active = BooleanField(default=True)
    email = CharField(max_length=255, unique=True)
    
    class Meta:
        table_name = "query_test_users"


async def test_queryset_debug():
    """Debug QuerySet issues."""
    print("🚀 QuerySet Debug Test")
    print("=" * 50)
    
    try:
        # Connect to SQLite
        engine = await connect("sqlite:///test_queryset_debug.db")
        print("✅ SQLite connection successful")
        
        # Create migration engine
        migration_engine = MigrationEngine(engine)
        
        # Generate migration
        print("🔄 Generating migration...")
        migration = await migration_engine.generate_migration_from_models(
            [QueryTestUser],
            "QuerySet debug migration",
            "test_runner"
        )
        
        if migration:
            print("✅ Migration generated successfully")
            print(f"Migration SQL:")
            print(migration.up_sql)
            print("\n" + "=" * 50)
            
            # Run migration
            print("🔄 Running migration...")
            result = await migration_engine.run_migrations()
            print(f"Migration result: {result}")
            
            if result.get('success'):
                print("✅ Migration executed successfully")
                
                # Set database for models
                print("🔄 Setting database for models...")
                set_database_for_models(engine)
                
                # Create test data
                print("🔄 Creating test data...")
                users = []
                for i in range(5):
                    user = QueryTestUser(
                        name=f"User {i+1}",
                        age=20 + i * 5,
                        is_active=i % 2 == 0,  # Alternate active/inactive
                        email=f"user{i+1}@example.com"
                    )
                    await user.save()
                    users.append(user)
                    print(f"   Created user: {user.name} (ID: {user.pk})")
                
                print(f"✅ Created {len(users)} test users")
                
                # Test 1: Basic QuerySet.all()
                print("\n🔄 Test 1: QuerySet.all()")
                try:
                    all_users = await QueryTestUser.all()
                    print(f"   Result: {len(all_users)} users found")
                    for user in all_users:
                        print(f"   - {user.name} (ID: {user.pk}, Age: {user.age})")
                except Exception as e:
                    print(f"   ❌ QuerySet.all() failed: {str(e)}")
                
                # Test 2: QuerySet.filter() with simple conditions
                print("\n🔄 Test 2: QuerySet.filter() - simple conditions")
                try:
                    active_users = await QueryTestUser.filter(is_active=True)
                    print(f"   Active users: {len(active_users)} found")
                    for user in active_users:
                        print(f"   - {user.name} (Active: {user.is_active})")
                except Exception as e:
                    print(f"   ❌ QuerySet.filter() failed: {str(e)}")
                
                # Test 3: QuerySet.filter() with field lookups
                print("\n🔄 Test 3: QuerySet.filter() - field lookups")
                try:
                    young_users = await QueryTestUser.filter(age__lt=25)
                    print(f"   Young users (age < 25): {len(young_users)} found")
                    for user in young_users:
                        print(f"   - {user.name} (Age: {user.age})")
                except Exception as e:
                    print(f"   ❌ QuerySet.filter() with lookups failed: {str(e)}")
                
                # Test 4: QuerySet.get() with conditions
                print("\n🔄 Test 4: QuerySet.get() with conditions")
                try:
                    user = await QueryTestUser.get(name="User 1")
                    print(f"   Found user: {user.name} (ID: {user.pk})")
                except Exception as e:
                    print(f"   ❌ QuerySet.get() failed: {str(e)}")
                
                # Test 5: QuerySet.count()
                print("\n🔄 Test 5: QuerySet.count()")
                try:
                    total_count = await QueryTestUser.count()
                    print(f"   Total users: {total_count}")
                    
                    active_count = await QueryTestUser.filter(is_active=True).count()
                    print(f"   Active users: {active_count}")
                except Exception as e:
                    print(f"   ❌ QuerySet.count() failed: {str(e)}")
                
                # Test 6: QuerySet.exists()
                print("\n🔄 Test 6: QuerySet.exists()")
                try:
                    has_active = await QueryTestUser.filter(is_active=True).exists()
                    print(f"   Has active users: {has_active}")
                    
                    has_old = await QueryTestUser.filter(age__gte=30).exists()
                    print(f"   Has users 30+: {has_old}")
                except Exception as e:
                    print(f"   ❌ QuerySet.exists() failed: {str(e)}")
                
                # Test 7: Q objects
                print("\n🔄 Test 7: Q objects")
                try:
                    from oxen.expressions import Q
                    complex_query = await QueryTestUser.filter(
                        Q(is_active=True) & Q(age__gte=20)
                    )
                    print(f"   Complex query result: {len(complex_query)} users")
                    for user in complex_query:
                        print(f"   - {user.name} (Active: {user.is_active}, Age: {user.age})")
                except Exception as e:
                    print(f"   ❌ Q objects failed: {str(e)}")
                
                # Test 8: Direct database query for comparison
                print("\n🔄 Test 8: Direct database query")
                try:
                    result = await engine.execute_query(
                        "SELECT * FROM query_test_users WHERE is_active = ?",
                        [True]
                    )
                    print(f"   Direct query result: {len(result.get('data', []))} users")
                    for record in result.get('data', []):
                        print(f"   - {record['name']} (Active: {record['is_active']})")
                except Exception as e:
                    print(f"   ❌ Direct query failed: {str(e)}")
                
                print("\n" + "=" * 50)
                print("📊 QuerySet Debug Results")
                print("=" * 50)
                print("This test identifies specific issues with the QuerySet system.")
                
            else:
                print(f"❌ Migration failed: {result}")
                
        else:
            print("❌ Migration generation failed")
            
    except Exception as e:
        print(f"❌ QuerySet debug test failed: {str(e)}")
    finally:
        try:
            await disconnect(engine)
        except:
            pass


async def main():
    """Main test function."""
    await test_queryset_debug()


if __name__ == "__main__":
    asyncio.run(main()) 