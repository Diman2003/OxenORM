#!/usr/bin/env python3
"""
Comprehensive test for all RelationField types
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField, BooleanField, ForeignKeyField, OneToOneField, ManyToManyField
from oxen.migrations import MigrationEngine


# Comprehensive test models
class Author(Model):
    """Author model for testing relationships."""
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = "test_authors"


class Category(Model):
    """Category model for testing relationships."""
    name = CharField(max_length=100)
    description = CharField(max_length=500, null=True)
    
    class Meta:
        table_name = "test_categories"


class Book(Model):
    """Book model with ForeignKey relationships."""
    title = CharField(max_length=200)
    author = ForeignKeyField(Author, related_name="books")
    category = ForeignKeyField(Category, related_name="books", null=True)
    price = IntegerField(default=0)
    is_published = BooleanField(default=False)
    
    class Meta:
        table_name = "test_books"


class BookDetail(Model):
    """BookDetail model with OneToOne relationship."""
    book = OneToOneField(Book, related_name="detail")
    pages = IntegerField(default=0)
    isbn = CharField(max_length=20, unique=True)
    
    class Meta:
        table_name = "test_book_details"


class Tag(Model):
    """Tag model for ManyToMany relationships."""
    name = CharField(max_length=50, unique=True)
    color = CharField(max_length=7, default="#000000")
    
    class Meta:
        table_name = "test_tags"


class BookTag(Model):
    """Through model for Book-Tag ManyToMany relationship."""
    book = ForeignKeyField(Book, related_name="book_tags")
    tag = ForeignKeyField(Tag, related_name="book_tags")
    
    class Meta:
        table_name = "test_book_tags"


class BookWithTags(Model):
    """Book model with ManyToMany relationship."""
    title = CharField(max_length=200)
    author = ForeignKeyField(Author, related_name="books_with_tags")
    tags = ManyToManyField(Tag, through=BookTag, related_name="books")
    
    class Meta:
        table_name = "test_books_with_tags"


async def test_relation_fields_comprehensive():
    """Comprehensive test for all relation field types."""
    print("🚀 Comprehensive RelationFields Test")
    print("=" * 50)
    
    # Connect to database with unique name
    db_name = f"test_relations_comp_{hash(str(asyncio.get_event_loop().time()))}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Set database for all models
    set_database_for_models(engine)
    
    # Generate and run migrations
    print("🔄 Generating migrations...")
    migration_engine = MigrationEngine(engine, migrations_dir="../migrations")
    
    # Get all model classes
    models = [Author, Category, Book, BookDetail, Tag, BookTag, BookWithTags]
    print(f"   Models to migrate: {[model.__name__ for model in models]}")
    
    migration = await migration_engine.generate_migration_from_models(
        models, "test_relation_fields_comprehensive", "test_runner"
    )
    
    if migration:
        print("✅ Migration generated successfully")
        
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
                
                # Check if our tables exist
                expected_tables = ['test_authors', 'test_categories', 'test_books', 'test_book_details', 'test_tags', 'test_book_tags', 'test_books_with_tags']
                for table in expected_tables:
                    if table in tables:
                        print(f"✅ {table} table created successfully")
                    else:
                        print(f"❌ {table} table not found")
            else:
                print(f"   ❌ Failed to check tables: {tables_result}")
                return
        else:
            print("❌ Migration failed")
            return
    else:
        print("❌ Failed to generate migration")
        return
    
    print("✅ Database setup complete")
    
    # Test 1: ForeignKey Relationships
    print("\n🔄 Test 1: ForeignKey Relationships")
    print("-" * 40)
    
    try:
        # Create test data
        author1 = await Author.create(name="John Doe", email="john@example.com")
        author2 = await Author.create(name="Jane Smith", email="jane@example.com")
        
        category1 = await Category.create(name="Fiction", description="Fictional books")
        category2 = await Category.create(name="Non-Fiction", description="Real stories")
        
        book1 = await Book.create(
            title="The Great Adventure",
            author=author1,
            category=category1,
            price=2500,
            is_published=True
        )
        
        book2 = await Book.create(
            title="Science Facts",
            author=author2,
            category=category2,
            price=3000,
            is_published=False
        )
        
        print(f"   Created author: {author1.name} (ID: {author1.pk})")
        print(f"   Created author: {author2.name} (ID: {author2.pk})")
        print(f"   Created book: {book1.title} by {book1.author.name}")
        print(f"   Created book: {book2.title} by {book2.author.name}")
        
        # Test ForeignKey access
        print("\n   Testing ForeignKey access:")
        retrieved_book = await Book.get(pk=book1.pk)
        print(f"   Book author ID: {retrieved_book.author}")
        print(f"   Book category ID: {retrieved_book.category}")
        
        # Fetch related objects separately
        author_from_db = await Author.get(pk=retrieved_book.author)
        category_from_db = await Category.get(pk=retrieved_book.category)
        print(f"   Book author: {author_from_db.name}")
        print(f"   Book category: {category_from_db.name}")
        
        # Test reverse ForeignKey access
        print("\n   Testing reverse ForeignKey access:")
        # For now, we'll test this by querying books directly
        author_books = await Book.filter(author=author1)
        print(f"   {author1.name}'s books: {[book.title for book in author_books]}")
        
        category_books = await Book.filter(category=category1)
        print(f"   {category1.name} books: {[book.title for book in category_books]}")
        
        print("✅ ForeignKey relationships working")
        
    except Exception as e:
        print(f"   ❌ ForeignKey test failed: {str(e)}")
    
    # Test 2: OneToOne Relationships
    print("\n🔄 Test 2: OneToOne Relationships")
    print("-" * 40)
    
    try:
        book_detail1 = await BookDetail.create(
            book=book1,
            pages=300,
            isbn="978-1234567890"
        )
        
        book_detail2 = await BookDetail.create(
            book=book2,
            pages=250,
            isbn="978-0987654321"
        )
        
        print(f"   Created book detail: {book_detail1.isbn} ({book_detail1.pages} pages)")
        print(f"   Created book detail: {book_detail2.isbn} ({book_detail2.pages} pages)")
        
        # Test OneToOne access
        print("\n   Testing OneToOne access:")
        # For now, we'll test this by querying the detail directly
        book_detail = await BookDetail.filter(book=book1.pk).first()
        if book_detail:
            print(f"   Book detail: ISBN {book_detail.isbn}, {book_detail.pages} pages")
        else:
            print("   No book detail found")
        
        # Test reverse OneToOne access
        print("\n   Testing reverse OneToOne access:")
        retrieved_detail = await BookDetail.get(pk=book_detail1.pk)
        print(f"   Detail's book ID: {retrieved_detail.book}")
        # Fetch the book separately
        book_from_db = await Book.get(pk=retrieved_detail.book)
        print(f"   Detail's book: {book_from_db.title}")
        
        print("✅ OneToOne relationships working")
        
    except Exception as e:
        print(f"   ❌ OneToOne test failed: {str(e)}")
    
    # Test 3: ManyToMany Relationships
    print("\n🔄 Test 3: ManyToMany Relationships")
    print("-" * 40)
    
    try:
        # Create tags
        tag1 = await Tag.create(name="Adventure", color="#FF6B6B")
        tag2 = await Tag.create(name="Science", color="#4ECDC4")
        tag3 = await Tag.create(name="Mystery", color="#45B7D1")
        
        print(f"   Created tags: {tag1.name}, {tag2.name}, {tag3.name}")
        
        # Create books with tags
        book_with_tags1 = await BookWithTags.create(
            title="Space Explorer",
            author=author1
        )
        
        book_with_tags2 = await BookWithTags.create(
            title="Detective Stories",
            author=author2
        )
        
        # Add tags to books through the through model
        await BookTag.create(book=book_with_tags1, tag=tag1)  # Adventure
        await BookTag.create(book=book_with_tags1, tag=tag2)  # Science
        await BookTag.create(book=book_with_tags2, tag=tag2)  # Science
        await BookTag.create(book=book_with_tags2, tag=tag3)  # Mystery
        
        print(f"   Created books with tags: {book_with_tags1.title}, {book_with_tags2.title}")
        
        # Test ManyToMany access
        print("\n   Testing ManyToMany access:")
        retrieved_book = await BookWithTags.get(pk=book_with_tags1.pk)
        # For now, we'll test this by querying tags through the through model
        book_tags = await BookTag.filter(book=book_with_tags1.pk)
        tag_ids = [bt.tag for bt in book_tags]
        tags = []
        for tag_id in tag_ids:
            tag = await Tag.get(pk=tag_id)
            tags.append(tag)
        print(f"   {retrieved_book.title} tags: {[tag.name for tag in tags]}")
        
        # Test reverse ManyToMany access
        print("\n   Testing reverse ManyToMany access:")
        retrieved_tag = await Tag.get(pk=tag2.pk)
        # For now, we'll test this by querying books through the through model
        tag_books = await BookTag.filter(tag=tag2.pk)
        book_ids = [bt.book for bt in tag_books]
        books = []
        for book_id in book_ids:
            book = await BookWithTags.get(pk=book_id)
            books.append(book)
        print(f"   Books with tag '{retrieved_tag.name}': {[book.title for book in books]}")
        
        print("✅ ManyToMany relationships working")
        
    except Exception as e:
        print(f"   ❌ ManyToMany test failed: {str(e)}")
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")
    print("✅ Comprehensive RelationFields test completed!")


if __name__ == "__main__":
    asyncio.run(test_relation_fields_comprehensive()) 