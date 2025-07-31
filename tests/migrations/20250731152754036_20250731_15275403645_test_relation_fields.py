"""
Migration: 20250731_15275403645_test_relation_fields

test_relation_fields

Generated on: 2025-07-31T09:57:54.036480
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="b781ee11-ca66-42ed-8b92-807d49bf15d4",
        name="20250731_15275403645_test_relation_fields",
        version="20250731152754036",
        up_sql="""-- Create table: test_authors
CREATE TABLE test_authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_categories
CREATE TABLE test_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_books
CREATE TABLE test_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    category INTEGER,
    price INTEGER NOT NULL DEFAULT 0,
    is_published BOOLEAN NOT NULL DEFAULT False,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_book_details
CREATE TABLE test_book_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_tags
CREATE TABLE test_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT '#000000',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_book_tags
CREATE TABLE test_book_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    tag INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_books_with_tags
CREATE TABLE test_books_with_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: test_books_with_tags
DROP TABLE IF EXISTS test_books_with_tags;

-- Drop table: test_book_tags
DROP TABLE IF EXISTS test_book_tags;

-- Drop table: test_tags
DROP TABLE IF EXISTS test_tags;

-- Drop table: test_book_details
DROP TABLE IF EXISTS test_book_details;

-- Drop table: test_books
DROP TABLE IF EXISTS test_books;

-- Drop table: test_categories
DROP TABLE IF EXISTS test_categories;

-- Drop table: test_authors
DROP TABLE IF EXISTS test_authors;
""",
        description="test_relation_fields",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="b781ee11-ca66-42ed-8b92-807d49bf15d4",
        name="20250731_15275403645_test_relation_fields",
        version="20250731152754036",
        up_sql="""-- Create table: test_authors
CREATE TABLE test_authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_categories
CREATE TABLE test_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_books
CREATE TABLE test_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    category INTEGER,
    price INTEGER NOT NULL DEFAULT 0,
    is_published BOOLEAN NOT NULL DEFAULT False,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_book_details
CREATE TABLE test_book_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_tags
CREATE TABLE test_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT '#000000',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_book_tags
CREATE TABLE test_book_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    tag INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_books_with_tags
CREATE TABLE test_books_with_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: test_books_with_tags
DROP TABLE IF EXISTS test_books_with_tags;

-- Drop table: test_book_tags
DROP TABLE IF EXISTS test_book_tags;

-- Drop table: test_tags
DROP TABLE IF EXISTS test_tags;

-- Drop table: test_book_details
DROP TABLE IF EXISTS test_book_details;

-- Drop table: test_books
DROP TABLE IF EXISTS test_books;

-- Drop table: test_categories
DROP TABLE IF EXISTS test_categories;

-- Drop table: test_authors
DROP TABLE IF EXISTS test_authors;
""",
        description="test_relation_fields",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
