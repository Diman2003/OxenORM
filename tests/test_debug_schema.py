#!/usr/bin/env python3
"""
Debug test to check database schema
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField
from oxen.fields.relational import ForeignKeyField
from oxen.migrations import MigrationEngine


# Simple test models
class Author(Model):
    """Author model for testing."""
    name = CharField(max_length=100)
    
    class Meta:
        table_name = f"authors_{uuid.uuid4().hex[:8]}"


class Book(Model):
    """Book model for testing."""
    title = CharField(max_length=200)
    author = ForeignKeyField(Author, related_name="books")
    
    class Meta:
        table_name = f"books_{uuid.uuid4().hex[:8]}"


async def debug_schema():
    """Debug the database schema."""
    print("🔍 Debug Schema Test")
    print("=" * 30)
    
    # Connect to database
    db_id = uuid.uuid4().hex[:8]
    db_name = f"test_debug_schema_{db_id}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Set database for all models
    set_database_for_models(engine)
    
    # Generate and run migrations
    print("🔄 Generating migrations...")
    migration_engine = MigrationEngine(engine, migrations_dir="../migrations")
    
    models = [Author, Book]
    migration = await migration_engine.generate_migration_from_models(
        models, f"test_debug_schema_{db_id}", "test_runner"
    )
    
    if migration:
        print("✅ Migration generated successfully")
        print(f"Migration SQL:\n{migration.up_sql}")
        
        print("🔄 Running migrations...")
        result = await migration_engine.run_migrations()
        print(f"Migration result: {result}")
        
        if result.get('success') or result.get('migrations_run', 0) > 0:
            print("✅ Migration executed successfully")
            
            # Check the actual schema
            print("\n🔍 Checking database schema...")
            schema_result = await engine.execute_query("SELECT sql FROM sqlite_master WHERE type='table'")
            print(f"Schema result: {schema_result}")
            
            if schema_result.get('data'):
                for row in schema_result['data']:
                    print(f"Table schema: {row[0]}")
        else:
            print("❌ Migration failed")
            return
    else:
        print("❌ Failed to generate migration")
        return
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")
    print("✅ Debug schema test completed!")


if __name__ == "__main__":
    asyncio.run(debug_schema()) 