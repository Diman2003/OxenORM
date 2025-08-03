#!/usr/bin/env python3
"""
Test for Advanced Relationships - Lazy Loading and Reverse Accessors
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField, BooleanField, DateTimeField
from oxen.fields.relational import ForeignKeyField, OneToOneField, ManyToManyField
from oxen.migrations import MigrationEngine


# Test models for advanced relationships
class Author(Model):
    """Author model for testing relationships."""
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    bio = CharField(max_length=500, null=True)
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = f"authors_{uuid.uuid4().hex[:8]}"


class Publisher(Model):
    """Publisher model for testing relationships."""
    name = CharField(max_length=100)
    address = CharField(max_length=200)
    phone = CharField(max_length=20, null=True)
    
    class Meta:
        table_name = f"publishers_{uuid.uuid4().hex[:8]}"


class Book(Model):
    """Book model for testing relationships."""
    title = CharField(max_length=200)
    author = ForeignKeyField(Author, related_name="books")
    publisher = ForeignKeyField(Publisher, related_name="published_books")
    isbn = CharField(max_length=13, unique=True)
    price = IntegerField(default=0)
    published_date = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"books_{uuid.uuid4().hex[:8]}"


class BookDetail(Model):
    """Book detail model for testing one-to-one relationships."""
    book = OneToOneField(Book, related_name="detail")
    pages = IntegerField(default=0)
    language = CharField(max_length=50, default="English")
    format = CharField(max_length=50, default="Paperback")
    
    class Meta:
        table_name = f"book_details_{uuid.uuid4().hex[:8]}"


class Category(Model):
    """Category model for testing many-to-many relationships."""
    name = CharField(max_length=100)
    description = CharField(max_length=500, null=True)
    
    class Meta:
        table_name = f"categories_{uuid.uuid4().hex[:8]}"


class BookCategory(Model):
    """Through model for book-category many-to-many relationship."""
    book = ForeignKeyField(Book, related_name="book_categories")
    category = ForeignKeyField(Category, related_name="category_books")
    
    class Meta:
        table_name = f"book_categories_{uuid.uuid4().hex[:8]}"


async def test_advanced_relationships():
    """Test advanced relationships with lazy loading and reverse accessors."""
    print("🚀 Advanced Relationships Test")
    print("=" * 40)
    
    # Connect to database with unique name
    db_id = uuid.uuid4().hex[:8]
    db_name = f"test_advanced_relationships_{db_id}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Set database for all models
    set_database_for_models(engine)
    
    # Generate and run migrations
    print("🔄 Generating migrations...")
    migration_engine = MigrationEngine(engine, migrations_dir="../migrations")
    
    models = [Author, Publisher, Book, BookDetail, Category, BookCategory]
    migration = await migration_engine.generate_migration_from_models(
        models, f"test_advanced_relationships_{db_id}", "test_runner"
    )
    
    if migration:
        print("✅ Migration generated successfully")
        
        print("🔄 Running migrations...")
        result = await migration_engine.run_migrations()
        print(f"Migration result: {result}")
        
        if result.get('success') or result.get('migrations_run', 0) > 0:
            print("✅ Migration executed successfully")
        else:
            print("❌ Migration failed")
            return
    else:
        print("❌ Failed to generate migration")
        return
    
    print("✅ Database setup complete")
    
    # Create test data
    print("\n🔄 Creating test data...")
    
    # Create authors
    author1 = await Author.create(
        name="John Smith",
        email="john@example.com",
        bio="Bestselling author of technical books"
    )
    author2 = await Author.create(
        name="Jane Doe",
        email="jane@example.com",
        bio="Award-winning fiction writer"
    )
    
    # Create publishers
    publisher1 = await Publisher.create(
        name="Tech Books Inc",
        address="123 Tech Street, Silicon Valley",
        phone="555-0123"
    )
    publisher2 = await Publisher.create(
        name="Fiction Press",
        address="456 Story Avenue, New York",
        phone="555-0456"
    )
    
    # Create categories
    tech_category = await Category.create(
        name="Technology",
        description="Books about technology and programming"
    )
    fiction_category = await Category.create(
        name="Fiction",
        description="Fictional literature"
    )
    business_category = await Category.create(
        name="Business",
        description="Business and management books"
    )
    
    # Create books
    book1 = await Book.create(
        title="Python Programming Guide",
        author=author1,
        publisher=publisher1,
        isbn="978-1234567890",
        price=2999
    )
    book2 = await Book.create(
        title="The Great Adventure",
        author=author2,
        publisher=publisher2,
        isbn="978-0987654321",
        price=1999
    )
    book3 = await Book.create(
        title="Advanced Python Techniques",
        author=author1,
        publisher=publisher1,
        isbn="978-1122334455",
        price=3999
    )
    
    # Create book details
    detail1 = await BookDetail.create(
        book=book1,
        pages=450,
        language="English",
        format="Hardcover"
    )
    detail2 = await BookDetail.create(
        book=book2,
        pages=320,
        language="English",
        format="Paperback"
    )
    
    # Create book-category relationships
    await BookCategory.create(book=book1, category=tech_category)
    await BookCategory.create(book=book1, category=business_category)
    await BookCategory.create(book=book2, category=fiction_category)
    await BookCategory.create(book=book3, category=tech_category)
    
    print("✅ Test data created")
    
    # Test 1: Lazy Loading - Foreign Key
    print("\n🔄 Test 1: Lazy Loading - Foreign Key")
    print("-" * 50)
    
    try:
        # Get a book and test lazy loading of author
        book = await Book.get(pk=book1.pk)
        print(f"   Book: {book.title}")
        print(f"   Author field type: {type(book.author)}")
        print(f"   Author representation: {book.author}")
        
        # Test lazy loading
        if hasattr(book.author, '_load'):
            print("   ✅ Lazy loading wrapper detected")
            
            # Load the author
            author = await book.author._load()
            print(f"   Loaded author: {author.name} ({author.email})")
            
            # Test accessing author properties
            print(f"   Author bio: {author.bio}")
            print(f"   Author active: {author.is_active}")
        else:
            print("   ❌ Lazy loading not working")
        
        print("✅ Lazy loading test completed")
        
    except Exception as e:
        print(f"   ❌ Lazy loading test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Reverse Accessors - Foreign Key
    print("\n🔄 Test 2: Reverse Accessors - Foreign Key")
    print("-" * 50)
    
    try:
        # Test reverse accessor from author to books
        author = await Author.get(pk=author1.pk)
        print(f"   Author: {author.name}")
        
        # Get books by this author using reverse accessor
        author_books = await author.books
        print(f"   Books by {author.name}: {len(author_books)}")
        
        for book in author_books:
            print(f"     - {book.title} (${book.price/100:.2f})")
        
        # Test reverse accessor from publisher to books
        publisher = await Publisher.get(pk=publisher1.pk)
        print(f"   Publisher: {publisher.name}")
        
        publisher_books = await publisher.published_books
        print(f"   Books published by {publisher.name}: {len(publisher_books)}")
        
        for book in publisher_books:
            print(f"     - {book.title} by {book.author}")
        
        print("✅ Reverse accessors test completed")
        
    except Exception as e:
        print(f"   ❌ Reverse accessors test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: One-to-One Relationships
    print("\n🔄 Test 3: One-to-One Relationships")
    print("-" * 50)
    
    try:
        # Test one-to-one relationship
        book = await Book.get(pk=book1.pk)
        print(f"   Book: {book.title}")
        
        # Get book detail using reverse accessor
        book_detail = await book.detail
        print(f"   Book detail: {book_detail.pages} pages, {book_detail.format}")
        
        # Test reverse accessor from detail to book
        detail = await BookDetail.get(pk=detail1.pk)
        # Load the book object first since it's lazy-loaded
        book = await detail.book._load()
        print(f"   Detail for: {book.title}")
        
        print("✅ One-to-one relationships test completed")
        
    except Exception as e:
        print(f"   ❌ One-to-one relationships test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Many-to-Many Relationships
    print("\n🔄 Test 4: Many-to-Many Relationships")
    print("-" * 50)
    
    try:
        # Test many-to-many through BookCategory
        book = await Book.get(pk=book1.pk)
        print(f"   Book: {book.title}")
        
        # Get categories for this book
        book_categories = await BookCategory.filter(book=book)
        print(f"   Categories for {book.title}: {len(book_categories)}")
        
        for book_category in book_categories:
            category = await Category.get(pk=book_category.category.pk)
            print(f"     - {category.name}: {category.description}")
        
        # Test reverse accessor from category to books
        tech_cat = await Category.get(pk=tech_category.pk)
        print(f"   Category: {tech_cat.name}")
        
        category_books = await BookCategory.filter(category=tech_cat)
        print(f"   Books in {tech_cat.name}: {len(category_books)}")
        
        for book_category in category_books:
            book = await Book.get(pk=book_category.book.pk)
            print(f"     - {book.title}")
        
        print("✅ Many-to-many relationships test completed")
        
    except Exception as e:
        print(f"   ❌ Many-to-many relationships test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Complex Relationship Queries
    print("\n🔄 Test 5: Complex Relationship Queries")
    print("-" * 50)
    
    try:
        # Find all books by authors with active status
        active_authors = await Author.filter(is_active=True)
        print(f"   Active authors: {len(active_authors)}")
        
        for author in active_authors:
            author_books = await author.books
            print(f"   {author.name} has {len(author_books)} books:")
            for book in author_books:
                print(f"     - {book.title} (${book.price/100:.2f})")
        
        # Find books published by publishers with phone numbers
        publishers_with_phone = await Publisher.filter(phone__isnull=False)
        print(f"   Publishers with phone: {len(publishers_with_phone)}")
        
        for publisher in publishers_with_phone:
            publisher_books = await publisher.published_books
            print(f"   {publisher.name} ({publisher.phone}) has {len(publisher_books)} books")
        
        print("✅ Complex relationship queries test completed")
        
    except Exception as e:
        print(f"   ❌ Complex relationship queries test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")
    print("✅ Advanced relationships test completed!")


if __name__ == "__main__":
    asyncio.run(test_advanced_relationships()) 