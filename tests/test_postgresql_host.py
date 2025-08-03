#!/usr/bin/env python3
"""
Test PostgreSQL with explicit host specification
"""

import asyncio
from oxen.rust_bridge import OxenEngine


async def test_postgresql_host():
    """Test PostgreSQL with explicit host."""
    print("🗄️  Testing PostgreSQL with Explicit Host...")
    
    # Test different connection string formats
    connection_strings = [
        "postgresql://oxenorm:oxenorm@127.0.0.1:5432/oxenorm",
        "postgresql://oxenorm:oxenorm@host.docker.internal:5432/oxenorm",
        "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm?sslmode=disable",
    ]
    
    for i, conn_str in enumerate(connection_strings, 1):
        print(f"\n🔗 Testing format {i}: {conn_str}")
        
        try:
            # Create Rust engine
            rust_engine = OxenEngine(conn_str)
            print("✅ Rust engine created")
            
            # Connect
            result = await rust_engine.connect()
            print(f"📊 Connect result: {result}")
            
            if result.get('success'):
                print("✅ Connection successful!")
                
                # Test basic query
                query_result = await rust_engine.execute_query("SELECT 1 as test")
                print(f"📊 Query result: {query_result}")
                
                if query_result.get('success'):
                    print("✅ Query successful!")
                    break
                else:
                    print(f"❌ Query failed: {query_result.get('error')}")
            else:
                print(f"❌ Connection failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")


async def main():
    """Main test function."""
    print("🚀 PostgreSQL Host Test")
    print("=" * 50)
    
    await test_postgresql_host()


if __name__ == "__main__":
    asyncio.run(main()) 