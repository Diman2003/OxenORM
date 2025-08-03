#!/usr/bin/env python3
"""
Debug Test for Engine Backend Selection

This test helps debug why the engine is not using the correct backend.
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import connect


async def test_debug_engine():
    """Debug the engine backend selection."""
    print("🚀 Engine Backend Debug Test")
    print("=" * 40)
    
    # Connect to database
    db_id = uuid.uuid4().hex[:8]
    db_name = f"test_debug_engine_{db_id}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Debug engine properties
    print(f"\n🔍 Engine Debug Info:")
    print(f"   db_type: {getattr(engine, 'db_type', 'N/A')}")
    print(f"   db_path: {getattr(engine, 'db_path', 'N/A')}")
    print(f"   rust_engine: {getattr(engine, 'rust_engine', 'N/A')}")
    print(f"   connection_string: {getattr(engine, 'connection_string', 'N/A')}")
    
    # Test the condition that determines backend selection
    print(f"\n🔍 Backend Selection Logic:")
    print(f"   self.db_type == 'sqlite': {getattr(engine, 'db_type', None) == 'sqlite'}")
    print(f"   self.rust_engine: {bool(getattr(engine, 'rust_engine', None))}")
    print(f"   Both conditions: {getattr(engine, 'db_type', None) == 'sqlite' and bool(getattr(engine, 'rust_engine', None))}")
    
    # Try to execute a query and see what happens
    print(f"\n🔄 Testing Query Execution:")
    try:
        result = await engine.execute_query("SELECT 1 as test")
        print(f"   Query Result: {result}")
    except Exception as e:
        print(f"   Query Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    await engine.disconnect()
    import os
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"\n🧹 Cleaned up database: {db_name}")
    
    print("\n✅ Debug test completed!")


if __name__ == "__main__":
    asyncio.run(test_debug_engine()) 