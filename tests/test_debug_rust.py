#!/usr/bin/env python3
"""
Debug test to check Rust backend database type detection
"""

import asyncio
from oxen.rust_bridge import OxenEngine


async def debug_rust_database_type():
    """Debug the Rust backend database type detection."""
    print("🔍 Debugging Rust Backend Database Type Detection...")
    
    # Test different connection strings
    connection_strings = [
        "sqlite:///test.db",
        "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm",
        "postgres://oxenorm:oxenorm@localhost:5432/oxenorm",
        "mysql://user:pass@localhost:3306/db",
    ]
    
    for conn_str in connection_strings:
        print(f"\n🔗 Testing: {conn_str}")
        
        try:
            # Create Rust engine
            rust_engine = OxenEngine(conn_str)
            print(f"✅ Rust engine created successfully")
            
            # Try to connect
            try:
                result = await rust_engine.connect()
                print(f"📊 Connect result: {result}")
                
                if result.get('success'):
                    print("✅ Connection successful!")
                    
                    # Test query
                    query_result = await rust_engine.execute_query("SELECT 1 as test")
                    print(f"📊 Query result: {query_result}")
                    
                else:
                    print(f"❌ Connection failed: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Connection error: {e}")
                
        except Exception as e:
            print(f"❌ Engine creation failed: {e}")


async def main():
    """Main debug function."""
    print("🚀 Rust Backend Database Type Debug Test")
    print("=" * 50)
    
    await debug_rust_database_type()


if __name__ == "__main__":
    asyncio.run(main()) 