#!/usr/bin/env python3
"""
Test migration runner directly
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import connect
from oxen.migrations.runner import MigrationRunner
from oxen.migrations.models import Migration, MigrationStatus


async def test_migration_runner():
    """Test migration runner directly."""
    print("🚀 Migration Runner Test")
    print("=" * 30)
    
    # Connect to database
    db_name = f"test_migration_runner_{hash(str(asyncio.get_event_loop().time()))}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Create migration runner
    runner = MigrationRunner(engine)
    
    # Ensure migrations table exists
    await runner._ensure_migrations_table()
    
    # Create a test migration
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
    
    migration = Migration(
        id="test-migration-id",
        name="test_migration",
        version="20250731160000000",
        up_sql=test_sql,
        down_sql="DROP TABLE IF EXISTS test_tags_debug; DROP TABLE IF EXISTS test_another_table;",
        description="Test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
    
    print("🔄 Running test migration...")
    
    # Record the migration
    await runner.record_migration(migration)
    
    # Run the migration
    success = await runner.run_migration(migration)
    
    if success:
        print("✅ Migration executed successfully")
        
        # Check what tables were created
        print("🔄 Checking created tables...")
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
    else:
        print("❌ Migration failed")
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")


if __name__ == "__main__":
    asyncio.run(test_migration_runner()) 