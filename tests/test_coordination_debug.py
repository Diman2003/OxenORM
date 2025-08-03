#!/usr/bin/env python3
"""
Coordination Debug Test
Debug the coordination between migrations and models
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import oxen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from oxen import connect, disconnect
from oxen.models import Model, set_database_for_models
from oxen.fields import CharField, IntegerField
from oxen.migrations import MigrationEngine


class CoordinationUser(Model):
    """Simple test model for coordination debugging."""
    name = CharField(max_length=100)
    age = IntegerField()
    
    class Meta:
        table_name = "coordination_users"


async def test_coordination_debug():
    """Debug coordination issues."""
    print("🚀 Coordination Debug Test")
    print("=" * 50)
    
    try:
        # Connect to SQLite
        engine = await connect("sqlite:///test_coordination.db")
        print("✅ SQLite connection successful")
        
        # Create migration engine
        migration_engine = MigrationEngine(engine)
        
        # Generate migration
        print("🔄 Generating migration...")
        migration = await migration_engine.generate_migration_from_models(
            [CoordinationUser],
            "Coordination debug migration",
            "test_runner"
        )
        
        if migration:
            print("✅ Migration generated successfully")
            print(f"Migration SQL:")
            print(migration.up_sql)
            print("\n" + "=" * 50)
            
            # Run migration
            print("🔄 Running migration...")
            result = await migration_engine.run_migrations()
            print(f"Migration result: {result}")
            
            if result.get('success'):
                print("✅ Migration executed successfully")
                
                # Set database for models
                print("🔄 Setting database for models...")
                set_database_for_models(engine)
                
                # Check if table exists directly
                print("🔄 Checking if table exists directly...")
                check_result = await engine.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='coordination_users'")
                print(f"Direct table check: {check_result}")
                
                if check_result.get('data'):
                    print("✅ Table exists in database!")
                    
                    # Try to insert directly
                    print("🔄 Testing direct insert...")
                    direct_insert = await engine.execute_query(
                        "INSERT INTO coordination_users (name, age) VALUES (?, ?)",
                        ["Direct Test", 25]
                    )
                    print(f"Direct insert result: {direct_insert}")
                    
                    # Now try model insert
                    print("🔄 Testing model insert...")
                    try:
                        user = CoordinationUser(name="Model Test", age=30)
                        await user.save()
                        print(f"✅ Model insert successful! ID: {user.pk}")
                    except Exception as e:
                        print(f"❌ Model insert failed: {str(e)}")
                        
                        # Check what database the model is using
                        print(f"Model database: {CoordinationUser._meta.db}")
                        print(f"Engine database: {engine}")
                        
                else:
                    print("❌ Table does not exist in database!")
                    
            else:
                print(f"❌ Migration failed: {result}")
                
        else:
            print("❌ Migration generation failed")
            
    except Exception as e:
        print(f"❌ Coordination debug test failed: {str(e)}")
    finally:
        try:
            await disconnect(engine)
        except:
            pass


async def main():
    """Main test function."""
    await test_coordination_debug()


if __name__ == "__main__":
    asyncio.run(main()) 