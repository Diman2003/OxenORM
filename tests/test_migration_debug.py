#!/usr/bin/env python3
"""
Debug test for migration execution
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField
from oxen.migrations import MigrationEngine


# Simple test model
class TestTag(Model):
    """Simple tag model."""
    name = CharField(max_length=50, unique=True)
    color = CharField(max_length=7, default="#000000")
    
    class Meta:
        table_name = "test_tags_debug"


async def test_migration_debug():
    """Debug migration execution."""
    print("🚀 Migration Debug Test")
    print("=" * 30)
    
    # Connect to database
    db_name = f"test_migration_debug_{hash(str(asyncio.get_event_loop().time()))}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Set database for all models
    set_database_for_models(engine)
    
    # Generate and run migrations
    print("🔄 Generating migrations...")
    migration_engine = MigrationEngine(engine, migrations_dir="../migrations")
    
    # Get model class
    models = [TestTag]
    print(f"   Models to migrate: {[model.__name__ for model in models]}")
    
    migration = await migration_engine.generate_migration_from_models(
        models, "test_migration_debug", "test_runner"
    )
    
    if migration:
        print("✅ Migration generated successfully")
        print(f"   Migration SQL: {migration.up_sql}")
        
        print("🔄 Running migrations...")
        result = await migration_engine.run_migrations()
        print(f"Migration result: {result}")
        
        if result.get('success'):
            print("✅ Migration executed successfully")
            
            # Check what tables were created
            print("🔄 Checking created tables...")
            tables_result = await engine.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            if tables_result.get('success'):
                tables = [row['name'] for row in tables_result.get('data', [])]
                print(f"   Created tables: {tables}")
                
                # Check if our table exists
                if 'test_tags_debug' in tables:
                    print("✅ test_tags_debug table created successfully")
                else:
                    print("❌ test_tags_debug table not found")
            else:
                print(f"   ❌ Failed to check tables: {tables_result}")
        else:
            print("❌ Migration failed")
            return
    else:
        print("❌ Failed to generate migration")
        return
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")


if __name__ == "__main__":
    asyncio.run(test_migration_debug()) 