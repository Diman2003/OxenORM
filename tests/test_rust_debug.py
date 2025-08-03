#!/usr/bin/env python3
"""
Debug test to check Rust backend integration
"""

import asyncio
import sys
from oxen import connect, disconnect
from oxen.rust_bridge import OxenEngine


async def debug_rust_backend():
    """Debug the Rust backend integration."""
    print("🔍 Debugging Rust Backend Integration...")
    
    try:
        # Test SQLite first (we know this works)
        print("\n🗄️  Testing SQLite with Rust backend...")
        sqlite_engine = await connect("sqlite:///debug_test.db")
        print(f"✅ SQLite connection successful: {type(sqlite_engine)}")
        
        # Test basic query
        result = await sqlite_engine.execute_query("SELECT 1 as test")
        print(f"📊 SQLite query result: {result}")
        
        # Check if it's using Rust backend
        if hasattr(sqlite_engine, '_rust_engine'):
            print("✅ SQLite is using Rust backend")
        else:
            print("❌ SQLite is NOT using Rust backend")
        
        await disconnect(sqlite_engine)
        
        # Test PostgreSQL
        print("\n🗄️  Testing PostgreSQL with Rust backend...")
        postgres_engine = await connect("postgresql://oxenorm:oxenorm@localhost:5432/oxenorm")
        print(f"✅ PostgreSQL connection successful: {type(postgres_engine)}")
        
        # Check if it's using Rust backend
        if hasattr(postgres_engine, '_rust_engine'):
            print("✅ PostgreSQL is using Rust backend")
        else:
            print("❌ PostgreSQL is NOT using Rust backend")
        
        # Test basic query
        result = await postgres_engine.execute_query("SELECT 1 as test")
        print(f"📊 PostgreSQL query result: {result}")
        
        await disconnect(postgres_engine)
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()


async def test_direct_rust_engine():
    """Test direct Rust engine usage."""
    print("\n🔧 Testing Direct Rust Engine...")
    
    try:
        # Create Rust engine directly
        rust_engine = OxenEngine("postgresql://oxenorm:oxenorm@localhost:5432/oxenorm")
        print(f"✅ Rust engine created: {rust_engine}")
        
        # Connect
        result = await rust_engine.connect()
        print(f"📊 Connect result: {result}")
        
        # Test query
        query_result = await rust_engine.execute_query("SELECT 1 as test")
        print(f"📊 Query result: {query_result}")
        
    except Exception as e:
        print(f"❌ Direct Rust engine test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main debug function."""
    print("🚀 Rust Backend Debug Test")
    print("=" * 50)
    
    await debug_rust_backend()
    await test_direct_rust_engine()


if __name__ == "__main__":
    asyncio.run(main()) 