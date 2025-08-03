#!/usr/bin/env python3
"""
Test uvloop integration with OxenORM
"""

import asyncio
import time
import sys
from oxen import configure_uvloop, is_uvloop_active, get_event_loop_info


async def test_uvloop_performance():
    """Test uvloop performance with simple async operations."""
    print("🧪 Testing uvloop integration with OxenORM...")
    
    # Get event loop info
    loop_info = get_event_loop_info()
    print(f"📊 Event Loop Info: {loop_info}")
    
    # Test basic async operations
    start_time = time.time()
    
    # Simulate some async operations
    tasks = []
    for i in range(1000):
        tasks.append(asyncio.sleep(0.001))
    
    await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"⏱️  Performance Test:")
    print(f"   - Duration: {duration:.4f} seconds")
    print(f"   - uvloop active: {is_uvloop_active()}")
    print(f"   - Loop type: {loop_info.get('loop_type', 'Unknown')}")
    
    if is_uvloop_active():
        print("✅ uvloop is active and providing enhanced performance!")
    else:
        print("⚠️  uvloop is not active - using standard asyncio")


async def test_database_operations():
    """Test database operations with uvloop."""
    print("\n🗄️  Testing database operations with uvloop...")
    
    try:
        from oxen import connect, disconnect
        from oxen.models import Model
        from oxen.fields import CharField, IntField
        
        # Define a simple model
        class TestUser(Model):
            username = CharField(max_length=100)
            age = IntField()
            
            class Meta:
                table_name = "test_users"
        
        # Connect to database
        engine = await connect("sqlite:///test_uvloop.db")
        print("✅ Database connected successfully")
        
        # Create table
        await TestUser.create_table()
        print("✅ Table created successfully")
        
        # Test CRUD operations
        start_time = time.time()
        
        # Create users
        users = []
        for i in range(100):
            user = await TestUser.create(username=f"user_{i}", age=20 + i)
            users.append(user)
        
        # Query users
        all_users = await TestUser.all()
        user_count = await TestUser.count()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Database operations completed:")
        print(f"   - Created {len(users)} users")
        print(f"   - Queried {len(all_users)} users")
        print(f"   - Count: {user_count}")
        print(f"   - Duration: {duration:.4f} seconds")
        print(f"   - uvloop active: {is_uvloop_active()}")
        
        # Cleanup
        await disconnect(engine)
        print("✅ Database disconnected")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")


def main():
    """Main test function."""
    print("🚀 OxenORM uvloop Integration Test")
    print("=" * 50)
    
    # Test 1: Basic uvloop functionality
    asyncio.run(test_uvloop_performance())
    
    # Test 2: Database operations with uvloop
    asyncio.run(test_database_operations())
    
    print("\n" + "=" * 50)
    print("✅ uvloop integration test completed!")
    
    # Print final status
    loop_info = get_event_loop_info()
    print(f"\n📊 Final Status:")
    print(f"   - uvloop available: {loop_info.get('uvloop_available', False)}")
    print(f"   - uvloop active: {is_uvloop_active()}")
    print(f"   - loop type: {loop_info.get('loop_type', 'Unknown')}")
    print(f"   - platform: {loop_info.get('platform', 'Unknown')}")


if __name__ == "__main__":
    main() 