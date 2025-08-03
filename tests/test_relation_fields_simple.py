#!/usr/bin/env python3
"""
Simple test for RelationFields to debug the issue
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField, ForeignKeyField
from oxen.migrations import MigrationEngine


# Simple test models
class SimpleAuthor(Model):
    """Simple author model."""
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    
    class Meta:
        table_name = "simple_authors"


class SimpleBook(Model):
    """Simple book model with ForeignKey."""
    title = CharField(max_length=200)
    author = ForeignKeyField(SimpleAuthor, related_name="books")
    price = IntegerField(default=0)
    
    class Meta:
        table_name = "simple_books"


async def test_simple_relations():
    """Simple test for relation fields."""
    print("🚀 Simple RelationFields Test")
    print("=" * 40)
    
    # Connect to database
    db_name = f"test_simple_relations_{hash(str(asyncio.get_event_loop().time()))}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Set database for all models
    set_database_for_models(engine)
    
    # Generate and run migrations
    print("🔄 Generating migrations...")
    migration_engine = MigrationEngine(engine, migrations_dir="../migrations")
    
    # Get all model classes
    models = [SimpleAuthor, SimpleBook]
    print(f"   Models to migrate: {[model.__name__ for model in models]}")
    
    migration = await migration_engine.generate_migration_from_models(
        models, "test_simple_relations", "test_runner"
    )
    
    if migration:
        print("✅ Migration generated successfully")
        print(f"   Migration SQL: {migration.up_sql[:200]}...")
        
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
            else:
                print(f"   ❌ Failed to check tables: {tables_result}")
        else:
            print("❌ Migration failed")
            return
    else:
        print("❌ Failed to generate migration")
        return
    
    print("✅ Database setup complete")
    
    # Test basic ForeignKey functionality
    print("\n🔄 Test: Basic ForeignKey Functionality")
    print("-" * 40)
    
    try:
        # Create author
        author = await SimpleAuthor.create(name="Test Author", email="test@example.com")
        print(f"   Created author: {author.name} (ID: {author.pk})")
        
        # Create book with ForeignKey
        book = await SimpleBook.create(
            title="Test Book",
            author=author,
            price=2500
        )
        print(f"   Created book: {book.title} by {book.author.name}")
        
        # Test ForeignKey access
        retrieved_book = await SimpleBook.get(pk=book.pk)
        print(f"   Retrieved book author ID: {retrieved_book.author}")
        
        # Fetch the author separately to verify the relationship
        author_from_db = await SimpleAuthor.get(pk=retrieved_book.author)
        print(f"   Retrieved book author: {author_from_db.name}")
        
        print("✅ Basic ForeignKey functionality working")
        
    except Exception as e:
        print(f"   ❌ ForeignKey test failed: {str(e)}")
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")


if __name__ == "__main__":
    asyncio.run(test_simple_relations()) 