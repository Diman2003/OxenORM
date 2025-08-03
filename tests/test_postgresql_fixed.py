#!/usr/bin/env python3
"""
Test PostgreSQL with different connection string formats
"""

import asyncio
from oxen import connect, disconnect


async def test_postgresql_formats():
    """Test different PostgreSQL connection string formats."""
    print("🗄️  Testing PostgreSQL Connection String Formats...")
    
    # Test different connection string formats
    connection_strings = [
        "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm",
        "postgres://oxenorm:oxenorm@localhost:5432/oxenorm",
        "postgresql://localhost:5432/oxenorm?user=oxenorm&password=oxenorm",
    ]
    
    for i, conn_str in enumerate(connection_strings, 1):
        print(f"\n🔗 Testing format {i}: {conn_str}")
        
        try:
            engine = await connect(conn_str)
            print(f"✅ Connection successful: {type(engine)}")
            
            # Test basic query
            result = await engine.execute_query("SELECT 1 as test")
            print(f"📊 Query result: {result}")
            
            if result.get('success'):
                print("✅ Query successful!")
            else:
                print(f"❌ Query failed: {result.get('error')}")
            
            await disconnect(engine)
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")


async def test_postgresql_direct():
    """Test direct PostgreSQL connection."""
    print("\n🔧 Testing Direct PostgreSQL Connection...")
    
    try:
        # Test with default PostgreSQL user
        engine = await connect("postgresql://postgres:postgres@localhost:5432/postgres")
        print(f"✅ Direct connection successful: {type(engine)}")
        
        # Test basic query
        result = await engine.execute_query("SELECT version() as version")
        print(f"📊 Version query result: {result}")
        
        if result.get('success'):
            print("✅ Version query successful!")
            data = result.get('data', [])
            if data:
                print(f"📊 PostgreSQL version: {data[0].get('version', 'Unknown')}")
        else:
            print(f"❌ Version query failed: {result.get('error')}")
        
        await disconnect(engine)
        
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")


async def main():
    """Main test function."""
    print("🚀 PostgreSQL Connection String Test")
    print("=" * 50)
    
    await test_postgresql_formats()
    await test_postgresql_direct()


if __name__ == "__main__":
    asyncio.run(main()) 