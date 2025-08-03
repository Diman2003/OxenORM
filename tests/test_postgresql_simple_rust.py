#!/usr/bin/env python3
"""
Simple PostgreSQL test with Rust backend
"""

import asyncio
from oxen.rust_bridge import OxenEngine


async def test_postgresql_rust():
    """Test PostgreSQL with Rust backend."""
    print("🗄️  Testing PostgreSQL with Rust Backend...")
    
    # Test with the working connection string
    connection_string = "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm"
    print(f"🔗 Connection string: {connection_string}")
    
    try:
        # Create Rust engine
        rust_engine = OxenEngine(connection_string)
        print("✅ Rust engine created")
        
        # Connect
        result = await rust_engine.connect()
        print(f"📊 Connect result: {result}")
        
        # Check if connection was successful (no error means success)
        if result.get('error') is None:
            print("✅ Connection successful!")
            
            # Test basic query
            query_result = await rust_engine.execute_query("SELECT 1 as test")
            print(f"📊 Query result: {query_result}")
            
            if query_result.get('error') is None:
                print("✅ Query successful!")
                
                # Test PostgreSQL version
                version_result = await rust_engine.execute_query("SELECT version() as version")
                print(f"📊 Version result: {version_result}")
                
                if version_result.get('error') is None:
                    data = version_result.get('data', [])
                    if data:
                        print(f"📊 PostgreSQL version: {data[0].get('version', 'Unknown')}")
                else:
                    print(f"❌ Version query failed: {version_result.get('error')}")
                
            else:
                print(f"❌ Query failed: {query_result.get('error')}")
        else:
            print(f"❌ Connection failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 PostgreSQL Rust Backend Test")
    print("=" * 50)
    
    await test_postgresql_rust()


if __name__ == "__main__":
    asyncio.run(main()) 