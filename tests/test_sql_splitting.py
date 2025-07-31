#!/usr/bin/env python3
"""
Test SQL splitting logic
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen.migrations.runner import MigrationRunner


def test_sql_splitting():
    """Test the SQL splitting logic."""
    print("🚀 SQL Splitting Test")
    print("=" * 30)
    
    # Create a dummy runner to test the splitting logic
    runner = MigrationRunner(None)
    
    # Test SQL with multiple statements
    test_sql = """-- Create table: test_tags_debug
CREATE TABLE test_tags_debug (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT "#000000",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_another_table
CREATE TABLE test_another_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL
);
"""
    
    print("Original SQL:")
    print(test_sql)
    print("\n" + "=" * 50)
    
    # Split the SQL
    statements = runner._split_sql_statements(test_sql)
    
    print("Split statements:")
    for i, statement in enumerate(statements, 1):
        print(f"\nStatement {i}:")
        print(statement)
        print("-" * 30)
        
        # Test if this statement can be executed
        print(f"Testing statement {i} execution...")
        try:
            import sqlite3
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()
            cursor.execute(statement)
            print(f"✅ Statement {i} is valid SQL")
            conn.close()
        except Exception as e:
            print(f"❌ Statement {i} failed: {e}")


if __name__ == "__main__":
    test_sql_splitting() 