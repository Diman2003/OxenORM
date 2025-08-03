#!/usr/bin/env python3
"""
Debug PostgreSQL connection issues
"""

import asyncio
from oxen import connect, disconnect
from oxen.uvloop_config import is_uvloop_active, get_event_loop_info


async def debug_postgresql():
    """Debug PostgreSQL connection."""
    print("🔍 Debugging PostgreSQL connection...")
    
    # Print uvloop status
    loop_info = get_event_loop_info()
    print(f"📊 Event Loop Info: {loop_info}")
    
    try:
        # Test connection string
        connection_string = "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm"
        print(f"🔗 Connection string: {connection_string}")
        
        # Try to connect
        print("🔄 Attempting to connect...")
        engine = await connect(connection_string)
        print("✅ Connection successful!")
        
        # Test basic query
        print("🔄 Testing basic query...")
        result = await engine.execute_query("SELECT 1 as test")
        print(f"📊 Query result: {result}")
        
        if result.get('error') is None:
            print("✅ Basic query successful!")
            
            # Test PostgreSQL version
            version_result = await engine.execute_query("SELECT version()")
            print(f"📊 Version result: {version_result}")
            
            if version_result.get('error') is None:
                version = version_result.get('data', [{}])[0].get('version', 'Unknown')
                print(f"✅ PostgreSQL version: {version}")
            else:
                print(f"❌ Version query failed: {version_result.get('error')}")
        else:
            print(f"❌ Basic query failed: {result.get('error')}")
        
        # Test table creation
        print("🔄 Testing table creation...")
        create_result = await engine.create_table("debug_test", {
            "id": "SERIAL PRIMARY KEY",
            "name": "VARCHAR(100) NOT NULL",
            "value": "INTEGER"
        })
        print(f"📊 Create table result: {create_result}")
        
        if create_result.get('error') is None:
            print("✅ Table creation successful!")
            
            # Test insert
            print("🔄 Testing insert...")
            insert_result = await engine.insert_record("debug_test", {
                "name": "test_item",
                "value": 42
            })
            print(f"📊 Insert result: {insert_result}")
            
            if insert_result.get('error') is None:
                print("✅ Insert successful!")
                
                # Test select
                print("🔄 Testing select...")
                select_result = await engine.select_records("debug_test")
                print(f"📊 Select result: {select_result}")
                
                if select_result.get('error') is None:
                    print("✅ Select successful!")
                    data = select_result.get('data', [])
                    print(f"📊 Retrieved {len(data)} records")
                    for record in data:
                        print(f"   - {record}")
                else:
                    print(f"❌ Select failed: {select_result.get('error')}")
            else:
                print(f"❌ Insert failed: {insert_result.get('error')}")
        else:
            print(f"❌ Table creation failed: {create_result.get('error')}")
        
        # Cleanup
        await engine.drop_table("debug_test")
        print("✅ Cleanup completed")
        
        return engine
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main debug function."""
    print("🚀 PostgreSQL Debug Test")
    print("=" * 50)
    
    engine = await debug_postgresql()
    
    if engine:
        print("\n" + "=" * 50)
        print("✅ Debug test completed!")
        
        # Cleanup
        await disconnect(engine)
        print("✅ Database disconnected")
    else:
        print("\n❌ Debug test failed!")


if __name__ == "__main__":
    asyncio.run(main()) 