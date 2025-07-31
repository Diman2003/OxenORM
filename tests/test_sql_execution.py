#!/usr/bin/env python3
"""
Test SQL execution manually
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import connect


async def test_sql_execution():
    """Test SQL execution manually."""
    print("🚀 SQL Execution Test")
    print("=" * 30)
    
    # Connect to database
    db_name = f"test_sql_execution_{hash(str(asyncio.get_event_loop().time()))}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Test SQL statements
    test_sql = """-- Create table: test_tags_debug
CREATE TABLE test_tags_debug (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT '#000000',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_another_table
CREATE TABLE test_another_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL
);
"""
    
    print("🔄 Executing SQL manually...")
    
    # Split and execute statements manually
    statements = []
    current_statement = ""
    in_string = False
    string_char = None
    
    for char in test_sql:
        if char in ['"', "'"] and (not in_string or char == string_char):
            if not in_string:
                in_string = True
                string_char = char
            else:
                in_string = False
                string_char = None
        elif char == ';' and not in_string:
            current_statement = current_statement.strip()
            if current_statement:
                statements.append(current_statement)
            current_statement = ""
        else:
            current_statement += char
    
    # Add the last statement if it's not empty
    current_statement = current_statement.strip()
    if current_statement:
        statements.append(current_statement)
    
    print(f"   Split into {len(statements)} statements")
    
    # Execute each statement
    for i, statement in enumerate(statements, 1):
        print(f"   Executing statement {i}: {statement[:50]}...")
        result = await engine.execute_query(statement)
        if result.get('error'):
            print(f"   ❌ Statement {i} failed: {result.get('error')}")
        else:
            print(f"   ✅ Statement {i} executed successfully")
    
    # Check what tables were created
    print("\n🔄 Checking created tables...")
    tables_result = await engine.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
    if tables_result.get('success'):
        tables = [row['name'] for row in tables_result.get('data', [])]
        print(f"   Created tables: {tables}")
        
        # Check if our tables exist
        if 'test_tags_debug' in tables:
            print("✅ test_tags_debug table created successfully")
        else:
            print("❌ test_tags_debug table not found")
            
        if 'test_another_table' in tables:
            print("✅ test_another_table created successfully")
        else:
            print("❌ test_another_table not found")
    else:
        print(f"   ❌ Failed to check tables: {tables_result}")
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")


if __name__ == "__main__":
    asyncio.run(test_sql_execution()) 