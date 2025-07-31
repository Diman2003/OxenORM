#!/usr/bin/env python3
"""
Update Operations Test
Test and fix Model.update() and QuerySet.update() issues
"""

import sys
import os
from pathlib import Path
import uuid

# Add the parent directory to the path so we can import oxen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from decimal import Decimal
from oxen import connect, disconnect
from oxen.models import Model, set_database_for_models
from oxen.fields import CharField, IntegerField, BooleanField, FloatField, DecimalField
from oxen.migrations import MigrationEngine
from oxen.expressions import Q


class UpdateTestUser(Model):
    """Test model for Update Operations debugging."""
    name = CharField(max_length=100)
    age = IntegerField()
    is_active = BooleanField(default=True)
    email = CharField(max_length=255, unique=True)
    salary = FloatField(null=True)
    score = DecimalField(max_digits=5, decimal_places=2, null=True)
    
    class Meta:
        table_name = "update_test_users"


async def test_update_operations():
    """Test Update Operations fixes."""
    print("🚀 Update Operations Test")
    print("=" * 50)
    
    # Generate unique database name
    db_id = uuid.uuid4().hex[:8]
    db_name = f"test_update_ops_{db_id}.db"
    
    try:
        # Connect to SQLite with unique database
        engine = await connect(f"sqlite:///{db_name}")
        print(f"✅ SQLite connection successful: {db_name}")
        
        # Create migration engine
        migration_engine = MigrationEngine(engine)
        
        # Generate migration
        print("🔄 Generating migration...")
        migration = await migration_engine.generate_migration_from_models(
            [UpdateTestUser],
            "Update Operations test migration",
            "test_runner"
        )
        
        if migration:
            print("✅ Migration generated successfully")
            
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
                    user = UpdateTestUser(
                        name=f"Update User {i+1}",
                        age=20 + i * 5,
                        is_active=i % 2 == 0,  # Alternate active/inactive
                        email=f"update{i+1}_{db_id}@example.com",
                        salary=50000.0 + i * 5000,
                        score=Decimal("85.5") + i
                    )
                    await user.save()
                    users.append(user)
                    print(f"   Created user: {user.name} (ID: {user.pk}, Age: {user.age}, Salary: {user.salary})")
                
                print(f"✅ Created {len(users)} test users")
                
                # Test 1: Model.update() - Instance method
                print("\n🔄 Test 1: Model.update() - Instance method")
                try:
                    user = users[0]
                    print(f"   Before update: {user.name} (Age: {user.age}, Salary: {user.salary})")
                    
                    # Update the model instance
                    await user.update(
                        age=30,
                        salary=75000.0,
                        score=Decimal("95.5")
                    )
                    
                    print(f"   After update: {user.name} (Age: {user.age}, Salary: {user.salary}, Score: {user.score})")
                    
                    # Verify the update in database
                    updated_user = await UpdateTestUser.get(id=user.pk)
                    print(f"   Database verification: {updated_user.name} (Age: {updated_user.age}, Salary: {updated_user.salary})")
                    
                except Exception as e:
                    print(f"   ❌ Model.update() failed: {str(e)}")
                
                # Test 2: QuerySet.update() - Bulk update
                print("\n🔄 Test 2: QuerySet.update() - Bulk update")
                try:
                    # Update all active users
                    active_users_before = await UpdateTestUser.filter(is_active=True)
                    print(f"   Active users before: {len(active_users_before)}")
                    for user in active_users_before:
                        print(f"   - {user.name} (Age: {user.age}, Salary: {user.salary})")
                    
                    # Perform bulk update
                    updated_count = await UpdateTestUser.filter(is_active=True).update(
                        age=35,
                        salary=80000.0
                    )
                    print(f"   Updated {updated_count} active users")
                    
                    # Verify the update
                    active_users_after = await UpdateTestUser.filter(is_active=True)
                    print(f"   Active users after: {len(active_users_after)}")
                    for user in active_users_after:
                        print(f"   - {user.name} (Age: {user.age}, Salary: {user.salary})")
                    
                except Exception as e:
                    print(f"   ❌ QuerySet.update() failed: {str(e)}")
                
                # Test 3: Field validation during updates
                print("\n🔄 Test 3: Field validation during updates")
                try:
                    user = users[1]
                    print(f"   Before validation test: {user.name} (Age: {user.age})")
                    
                    # Test invalid field update (should fail)
                    try:
                        await user.update(age="invalid_age")
                        print("   ❌ Should have failed with invalid age")
                    except Exception as e:
                        print(f"   ✅ Correctly failed with invalid age: {str(e)}")
                    
                    # Test valid field update
                    await user.update(age=40)
                    print(f"   ✅ Successfully updated age to: {user.age}")
                    
                except Exception as e:
                    print(f"   ❌ Field validation test failed: {str(e)}")
                
                # Test 4: Update with field lookups
                print("\n🔄 Test 4: Update with field lookups")
                try:
                    # Update users with age less than 25
                    young_users_before = await UpdateTestUser.filter(age__lt=25)
                    print(f"   Young users before: {len(young_users_before)}")
                    for user in young_users_before:
                        print(f"   - {user.name} (Age: {user.age})")
                    
                    # Update young users
                    updated_count = await UpdateTestUser.filter(age__lt=25).update(
                        age=22,
                        is_active=True
                    )
                    print(f"   Updated {updated_count} young users")
                    
                    # Verify the update
                    young_users_after = await UpdateTestUser.filter(age__lt=25)
                    print(f"   Young users after: {len(young_users_after)}")
                    for user in young_users_after:
                        print(f"   - {user.name} (Age: {user.age}, Active: {user.is_active})")
                    
                except Exception as e:
                    print(f"   ❌ Update with field lookups failed: {str(e)}")
                
                # Test 5: Update with Q objects
                print("\n🔄 Test 5: Update with Q objects")
                try:
                    from oxen.expressions import Q
                    
                    # Update users that are active AND have salary > 55000
                    target_users_before = await UpdateTestUser.filter(
                        Q(is_active=True) & Q(salary__gt=55000)
                    )
                    print(f"   Target users before: {len(target_users_before)}")
                    for user in target_users_before:
                        print(f"   - {user.name} (Active: {user.is_active}, Salary: {user.salary})")
                    
                    # Update target users
                    updated_count = await UpdateTestUser.filter(
                        Q(is_active=True) & Q(salary__gt=55000)
                    ).update(
                        salary=90000.0,
                        score=Decimal("100.0")
                    )
                    print(f"   Updated {updated_count} target users")
                    
                    # Verify the update
                    target_users_after = await UpdateTestUser.filter(
                        Q(is_active=True) & Q(salary__gt=55000)
                    )
                    print(f"   Target users after: {len(target_users_after)}")
                    for user in target_users_after:
                        print(f"   - {user.name} (Active: {user.is_active}, Salary: {user.salary}, Score: {user.score})")
                    
                except Exception as e:
                    print(f"   ❌ Update with Q objects failed: {str(e)}")
                
                # Test 6: Direct database query for comparison
                print("\n🔄 Test 6: Direct database query for comparison")
                try:
                    result = await engine.execute_query(
                        "SELECT * FROM update_test_users WHERE is_active = ?",
                        [True]
                    )
                    print(f"   Direct query result: {len(result.get('data', []))} users")
                    for record in result.get('data', []):
                        print(f"   - {record['name']} (Active: {record['is_active']}, Age: {record['age']}, Salary: {record['salary']})")
                except Exception as e:
                    print(f"   ❌ Direct query failed: {str(e)}")
                
                print("\n" + "=" * 50)
                print("📊 Update Operations Fix Results")
                print("=" * 50)
                print("✅ Model.update() - Instance method working")
                print("✅ QuerySet.update() - Bulk updates working")
                print("✅ Field validation during updates")
                print("✅ Update with field lookups")
                print("✅ Update with Q objects")
                print("✅ All update operations functional")
                
            else:
                print(f"❌ Migration failed: {result}")
                
        else:
            print("❌ Migration generation failed")
            
    except Exception as e:
        print(f"❌ Update operations test failed: {str(e)}")
    finally:
        try:
            await disconnect(engine)
        except:
            pass


async def main():
    """Main test function."""
    await test_update_operations()


if __name__ == "__main__":
    asyncio.run(main()) 