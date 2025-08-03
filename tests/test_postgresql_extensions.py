#!/usr/bin/env python3
"""
PostgreSQL Extensions Test
Tests PostgreSQL extensions (PostGIS, hstore) for advanced field types
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
from oxen.exceptions import OperationalError


class PostGISUser(Model):
    """Test model with PostgreSQL-specific field types."""
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
        table_name = "postgis_users"


async def test_postgresql_extensions():
    """Test PostgreSQL extensions and advanced field types."""
    print("🚀 Testing PostgreSQL Extensions")
    print("=" * 50)
    
    try:
        # Connect to PostgreSQL
        engine = await connect("postgresql://oxenorm:oxenorm@localhost:5432/oxenorm")
        print("✅ PostgreSQL connection successful")
        
        # Enable extensions
        print("🔄 Enabling PostgreSQL extensions...")
        
        # Enable hstore extension
        hstore_result = await engine.execute_query("CREATE EXTENSION IF NOT EXISTS hstore")
        if hstore_result.get('success'):
            print("✅ hstore extension enabled")
        else:
            print(f"⚠️  hstore extension warning: {hstore_result.get('error')}")
        
        # Enable PostGIS extension
        postgis_result = await engine.execute_query("CREATE EXTENSION IF NOT EXISTS postgis")
        if postgis_result.get('success'):
            print("✅ PostGIS extension enabled")
        else:
            print(f"⚠️  PostGIS extension warning: {postgis_result.get('error')}")
        
        # Test CRUD operations with advanced field types
        await test_advanced_crud_operations(engine)
        
    except Exception as e:
        print(f"❌ PostgreSQL extensions test failed: {str(e)}")
    finally:
        # Cleanup
        try:
            await disconnect(engine)
        except:
            pass


async def test_advanced_crud_operations(engine):
    """Test CRUD operations with PostgreSQL-specific field types."""
    print("🔄 Testing advanced CRUD operations...")
    
    # Test User creation with advanced fields
    test_user = PostGISUser(
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
            "level": "Senior",
            "location": "San Francisco"
        },
        jsonb_data={
            "preferences": {
                "theme": "dark",
                "notifications": True,
                "language": "en"
            },
            "settings": {
                "auto_save": True,
                "sync_interval": 300
            }
        }
    )
    
    # Save user
    await test_user.save()
    print(f"✅ User created with ID: {test_user.pk}")
    
    # Retrieve user
    retrieved_user = await PostGISUser.get(id=test_user.pk)
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
    
    # Test queries with advanced field types
    all_users = await PostGISUser.all()
    print(f"✅ Retrieved {len(all_users)} users")
    
    # Test filtering with JSON fields
    users_with_skills = await PostGISUser.filter(profile_data__contains={"skills": ["Python"]})
    print(f"✅ Found {len(users_with_skills)} users with Python skills")
    
    # Test counting
    user_count = await PostGISUser.count()
    print(f"✅ Total users: {user_count}")
    
    # Test exists
    user_exists = await PostGISUser.exists(id=test_user.pk)
    print(f"✅ User exists: {user_exists}")


async def test_postgresql_specific_features():
    """Test PostgreSQL-specific features."""
    print("\n🔍 Testing PostgreSQL-Specific Features...")
    
    try:
        # Connect to PostgreSQL
        engine = await connect("postgresql://oxenorm:oxenorm@localhost:5432/oxenorm")
        
        # Test JSONB operations
        print("🔄 Testing JSONB operations...")
        
        # Test JSONB containment
        jsonb_test = await engine.execute_query("""
            SELECT '{"a": 1, "b": 2}'::jsonb @> '{"a": 1}'::jsonb as contains_test
        """)
        if jsonb_test.get('success'):
            print("✅ JSONB containment test successful")
        
        # Test hstore operations
        print("🔄 Testing hstore operations...")
        hstore_test = await engine.execute_query("""
            SELECT 'a=>1, b=>2'::hstore ? 'a' as hstore_test
        """)
        if hstore_test.get('success'):
            print("✅ hstore operations test successful")
        
        # Test PostGIS operations (if available)
        print("🔄 Testing PostGIS operations...")
        postgis_test = await engine.execute_query("""
            SELECT ST_AsText(ST_GeomFromText('POINT(0 0)')) as postgis_test
        """)
        if postgis_test.get('success'):
            print("✅ PostGIS operations test successful")
        
    except Exception as e:
        print(f"❌ PostgreSQL-specific features test failed: {str(e)}")
    finally:
        try:
            await disconnect(engine)
        except:
            pass


async def main():
    """Main test function."""
    print("🚀 PostgreSQL Extensions and Advanced Features Test")
    print("=" * 70)
    
    # Test PostgreSQL extensions
    await test_postgresql_extensions()
    
    # Test PostgreSQL-specific features
    await test_postgresql_specific_features()
    
    print("\n" + "=" * 70)
    print("✅ PostgreSQL Extensions Test Completed!")


if __name__ == "__main__":
    asyncio.run(main()) 