#!/usr/bin/env python3
"""
Test SQL execution through engine
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import connect


async def test_engine_sql():
    """Test SQL execution through engine."""
    print("🚀 Engine SQL Test")
    print("=" * 30)
    
    # Connect to database
    db_name = f"test_engine_sql_{hash(str(asyncio.get_event_loop().time()))}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Test SQL with double quotes
    test_sql = """CREATE TABLE test_tags_debug (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT "#000000",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""
    
    print("🔄 Executing SQL through engine...")
    print(f"SQL: {test_sql}")
    
    result = await engine.execute_query(test_sql)
    print(f"Result: {result}")
    
    if result.get('error'):
        print(f"❌ SQL execution failed: {result.get('error')}")
    else:
        print("✅ SQL executed successfully")
        
        # Check if table was created
        tables_result = await engine.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='test_tags_debug';")
        if tables_result.get('success') and tables_result.get('data'):
            print("✅ Table created successfully")
        else:
            print("❌ Table not found")
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")


if __name__ == "__main__":
    asyncio.run(test_engine_sql()) 