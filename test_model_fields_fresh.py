#!/usr/bin/env python3
"""
Fresh test for model fields with unique data
"""

import asyncio
import uuid
from datetime import datetime, date, time
from decimal import Decimal
from oxen import connect, disconnect
from oxen.models import Model
from oxen.fields.data import (
    CharField, TextField, IntegerField, FloatField, DecimalField,
    BooleanField, DateTimeField, DateField, TimeField, JSONField
)


class SimpleUser(Model):
    """Simple test model with basic field types."""
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100)
    age = IntegerField()
    height = FloatField()
    salary = DecimalField(max_digits=10, decimal_places=2)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    birth_date = DateField()
    work_time = TimeField()
    profile = JSONField(null=True)
    
    class Meta:
        table_name = "simple_users"


async def create_tables(engine):
    """Create tables for the models."""
    print("🔄 Creating tables...")
    
    # Drop existing table first
    drop_sql = "DROP TABLE IF EXISTS simple_users"
    await engine.execute_query(drop_sql)
    
    # Create simple_users table
    create_sql = """
    CREATE TABLE IF NOT EXISTS simple_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) NOT NULL,
        age INTEGER NOT NULL,
        height REAL NOT NULL,
        salary DECIMAL(10,2) NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        birth_date DATE NOT NULL,
        work_time TIME NOT NULL,
        profile TEXT
    )
    """
    
    result = await engine.execute_query(create_sql)
    if result.get('error') is None:
        print("✅ simple_users table created successfully")
    else:
        print(f"❌ Failed to create table: {result.get('error')}")


async def test_sqlite_fresh():
    """Test basic field types with SQLite and fresh data."""
    print("🗄️  Testing SQLite with Fresh Data...")
    
    try:
        # Connect to SQLite
        engine = await connect("sqlite:///test_fresh.db")
        print("✅ SQLite connection successful")
        
        # Create tables
        await create_tables(engine)
        
        # Generate unique test data
        unique_id = str(uuid.uuid4())[:8]
        test_data = {
            'username': f'test_user_{unique_id}',
            'email': f'test_{unique_id}@example.com',
            'age': 25,
            'height': 175.5,
            'salary': Decimal('50000.00'),
            'is_active': True,
            'birth_date': date(1998, 1, 1),
            'work_time': time(9, 0, 0),
            'profile': {'skills': ['Python'], 'experience': 2}
        }
        
        # Create user
        user = SimpleUser(**test_data)
        await user.save()
        print(f"✅ User created with ID: {user.pk}")
        
        # Verify user was saved
        retrieved_user = await SimpleUser.get(pk=user.pk)
        print("✅ User retrieved successfully")
        
        # Check basic fields
        print(f"✅ Username: {retrieved_user.username}")
        print(f"✅ Email: {retrieved_user.email}")
        print(f"✅ Age: {retrieved_user.age}")
        print(f"✅ Height: {retrieved_user.height}")
        print(f"✅ Salary: {retrieved_user.salary}")
        print(f"✅ Is Active: {retrieved_user.is_active}")
        print(f"✅ Birth Date: {retrieved_user.birth_date}")
        print(f"✅ Work Time: {retrieved_user.work_time}")
        print(f"✅ Profile: {retrieved_user.profile}")
        
        await disconnect(engine)
        return True
        
    except Exception as e:
        print(f"❌ SQLite test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def create_postgresql_tables(engine):
    """Create tables for PostgreSQL."""
    print("🔄 Creating PostgreSQL tables...")
    
    # Drop existing table first
    drop_sql = "DROP TABLE IF EXISTS simple_users"
    await engine.execute_query(drop_sql)
    
    # Create simple_users table for PostgreSQL
    create_sql = """
    CREATE TABLE IF NOT EXISTS simple_users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) NOT NULL,
        age INTEGER NOT NULL,
        height REAL NOT NULL,
        salary DECIMAL(10,2) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        birth_date DATE NOT NULL,
        work_time TIME NOT NULL,
        profile JSONB
    )
    """
    
    result = await engine.execute_query(create_sql)
    if result.get('error') is None:
        print("✅ simple_users table created successfully")
    else:
        print(f"❌ Failed to create table: {result.get('error')}")


async def test_postgresql_fresh():
    """Test basic field types with PostgreSQL and fresh data."""
    print("\n🗄️  Testing PostgreSQL with Fresh Data...")
    
    try:
        # Connect to PostgreSQL
        engine = await connect("postgresql://oxenorm:oxenorm@localhost:5432/oxenorm")
        print("✅ PostgreSQL connection successful")
        
        # Create tables
        await create_postgresql_tables(engine)
        
        # Generate unique test data
        unique_id = str(uuid.uuid4())[:8]
        test_data = {
            'username': f'postgres_user_{unique_id}',
            'email': f'postgres_{unique_id}@example.com',
            'age': 30,
            'height': 180.0,
            'salary': Decimal('75000.00'),
            'is_active': True,
            'birth_date': date(1993, 5, 15),
            'work_time': time(8, 30, 0),
            'profile': {'skills': ['PostgreSQL', 'Python'], 'experience': 5}
        }
        
        # Create user
        user = SimpleUser(**test_data)
        await user.save()
        print(f"✅ User created with ID: {user.pk}")
        
        # Verify user was saved
        retrieved_user = await SimpleUser.get(pk=user.pk)
        print("✅ User retrieved successfully")
        
        # Check basic fields
        print(f"✅ Username: {retrieved_user.username}")
        print(f"✅ Email: {retrieved_user.email}")
        print(f"✅ Age: {retrieved_user.age}")
        print(f"✅ Height: {retrieved_user.height}")
        print(f"✅ Salary: {retrieved_user.salary}")
        print(f"✅ Is Active: {retrieved_user.is_active}")
        print(f"✅ Birth Date: {retrieved_user.birth_date}")
        print(f"✅ Work Time: {retrieved_user.work_time}")
        print(f"✅ Profile: {retrieved_user.profile}")
        
        await disconnect(engine)
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Model Fields Test with Fresh Data")
    print("=" * 60)
    
    results = []
    
    # Test SQLite
    results.append(await test_sqlite_fresh())
    
    # Test PostgreSQL
    results.append(await test_postgresql_fresh())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"✅ SQLite Fresh Data: {'PASS' if results[0] else 'FAIL'}")
    print(f"✅ PostgreSQL Fresh Data: {'PASS' if results[1] else 'FAIL'}")
    
    if all(results):
        print("\n🎉 All model field tests passed!")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 