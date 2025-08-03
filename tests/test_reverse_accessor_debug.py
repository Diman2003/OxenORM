#!/usr/bin/env python3
"""
Debug test for reverse accessor setup
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


async def debug_reverse_accessor():
    """Debug the reverse accessor setup."""
    print("🔍 Debug Reverse Accessor Test")
    print("=" * 40)
    
    # Check if reverse accessor is set up
    print("🔍 Checking reverse accessor setup...")
    
    # Check if Author has the books attribute
    if hasattr(Author, 'books'):
        print(f"✅ Author.books exists: {type(Author.books)}")
        print(f"   Author.books: {Author.books}")
    else:
        print("❌ Author.books does not exist")
    
    # Check if Book has the author attribute
    if hasattr(Book, 'author'):
        print(f"✅ Book.author exists: {type(Book.author)}")
    else:
        print("❌ Book.author does not exist")
    
    # Check the field setup
    print("\n🔍 Checking field setup...")
    print(f"Book._meta.fk_fields: {Book._meta.fk_fields}")
    print(f"Book._meta.fields_map['author']: {Book._meta.fields_map['author']}")
    
    # Check if the reverse accessor was set up
    if hasattr(Author, 'books'):
        print(f"Author.books.model_class: {Author.books.model_class}")
        print(f"Author.books.related_field: {Author.books.related_field}")
        print(f"Author.books.related_model: {Author.books.related_model}")
    
    print("✅ Debug reverse accessor test completed!")


if __name__ == "__main__":
    asyncio.run(debug_reverse_accessor()) 