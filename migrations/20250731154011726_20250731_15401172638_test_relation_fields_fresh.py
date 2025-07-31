"""
Migration: 20250731_15401172638_test_relation_fields_fresh

test_relation_fields_fresh

Generated on: 2025-07-31T10:10:11.726414
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="246e7bc9-2655-4a9a-9b03-900ca592d18b",
        name="20250731_15401172638_test_relation_fields_fresh",
        version="20250731154011726",
        up_sql="""-- Create table: simple_authors
CREATE TABLE simple_authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_books
CREATE TABLE simple_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    price INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_book_details
CREATE TABLE simple_book_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_tags
CREATE TABLE simple_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT "#000000",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_book_tags
CREATE TABLE simple_book_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    tag INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simple_book_tags
DROP TABLE IF EXISTS simple_book_tags;

-- Drop table: simple_tags
DROP TABLE IF EXISTS simple_tags;

-- Drop table: simple_book_details
DROP TABLE IF EXISTS simple_book_details;

-- Drop table: simple_books
DROP TABLE IF EXISTS simple_books;

-- Drop table: simple_authors
DROP TABLE IF EXISTS simple_authors;
""",
        description="test_relation_fields_fresh",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="246e7bc9-2655-4a9a-9b03-900ca592d18b",
        name="20250731_15401172638_test_relation_fields_fresh",
        version="20250731154011726",
        up_sql="""-- Create table: simple_authors
CREATE TABLE simple_authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_books
CREATE TABLE simple_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    price INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_book_details
CREATE TABLE simple_book_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_tags
CREATE TABLE simple_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT "#000000",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_book_tags
CREATE TABLE simple_book_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    tag INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simple_book_tags
DROP TABLE IF EXISTS simple_book_tags;

-- Drop table: simple_tags
DROP TABLE IF EXISTS simple_tags;

-- Drop table: simple_book_details
DROP TABLE IF EXISTS simple_book_details;

-- Drop table: simple_books
DROP TABLE IF EXISTS simple_books;

-- Drop table: simple_authors
DROP TABLE IF EXISTS simple_authors;
""",
        description="test_relation_fields_fresh",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
