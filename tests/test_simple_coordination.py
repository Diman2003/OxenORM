#!/usr/bin/env python3
"""
Simple Coordination Test
Test the coordination fix with explicit database setting
"""

import asyncio
import uuid
from datetime import date
from decimal import Decimal

from oxen import connect, disconnect
from oxen.models import Model
from oxen.fields import CharField, IntegerField, FloatField, DecimalField, BooleanField, DateField, UUIDField, JSONField
from oxen.migrations import MigrationEngine


class SimpleUser(Model):
    """Simple test model."""
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


async def test_simple_coordination():
    """Test simple coordination fix."""
    print("🚀 Simple Coordination Test")
    print("=" * 50)
    
    try:
        # Connect to SQLite
        engine = await connect("sqlite:///test_simple_coordination.db")
        print("✅ SQLite connection successful")
        
        # Create migration engine
        migration_engine = MigrationEngine(engine)
        
        # Generate migration
        print("🔄 Generating migration...")
        migration = await migration_engine.generate_migration_from_models(
            [SimpleUser],
            "Simple coordination migration",
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
                
                # Explicitly set database for the model
                print("🔄 Setting database for model...")
                SimpleUser._meta.db = engine
                
                # Test CRUD operations
                print("🔄 Testing CRUD operations...")
                
                # Create user
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
                
                # Test queries
                all_users = await SimpleUser.all()
                print(f"✅ Retrieved {len(all_users)} users")
                
                # Test filtering
                active_users = await SimpleUser.filter(is_active=True)
                print(f"✅ Found {len(active_users)} active users")
                
                # Test counting
                user_count = await SimpleUser.count()
                print(f"✅ Total users: {user_count}")
                
                # Test exists
                user_exists = await SimpleUser.exists(id=test_user.pk)
                print(f"✅ User exists: {user_exists}")
                
                print("🎉 ALL CRUD OPERATIONS SUCCESSFUL!")
                
            else:
                print(f"❌ Migration failed: {result}")
                
        else:
            print("❌ Migration generation failed")
            
    except Exception as e:
        print(f"❌ Simple coordination test failed: {str(e)}")
    finally:
        try:
            await disconnect(engine)
        except:
            pass


async def main():
    """Main test function."""
    await test_simple_coordination()


if __name__ == "__main__":
    asyncio.run(main()) 