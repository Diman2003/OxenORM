"""
Migration: 20250803_21383276679_test_advanced_relationships_c2519235

test_advanced_relationships_c2519235

Generated on: 2025-08-03T16:08:32.766827
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="6d9c1221-664b-40a1-8b31-33314b793a00",
        name="20250803_21383276679_test_advanced_relationships_c2519235",
        version="20250803213832766",
        up_sql="""-- Create table: authors_16398b64
CREATE TABLE authors_16398b64 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_d12c36f9
CREATE TABLE publishers_d12c36f9 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_f5c8a1c4
CREATE TABLE books_f5c8a1c4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    publisher INTEGER,
    isbn VARCHAR(13) NOT NULL UNIQUE,
    price INTEGER NOT NULL DEFAULT 0,
    published_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_details_f7f222b0
CREATE TABLE book_details_f7f222b0 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_3ac27544
CREATE TABLE categories_3ac27544 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_91d36ff6
CREATE TABLE book_categories_91d36ff6 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_91d36ff6
DROP TABLE IF EXISTS book_categories_91d36ff6;

-- Drop table: categories_3ac27544
DROP TABLE IF EXISTS categories_3ac27544;

-- Drop table: book_details_f7f222b0
DROP TABLE IF EXISTS book_details_f7f222b0;

-- Drop table: books_f5c8a1c4
DROP TABLE IF EXISTS books_f5c8a1c4;

-- Drop table: publishers_d12c36f9
DROP TABLE IF EXISTS publishers_d12c36f9;

-- Drop table: authors_16398b64
DROP TABLE IF EXISTS authors_16398b64;
""",
        description="test_advanced_relationships_c2519235",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="6d9c1221-664b-40a1-8b31-33314b793a00",
        name="20250803_21383276679_test_advanced_relationships_c2519235",
        version="20250803213832766",
        up_sql="""-- Create table: authors_16398b64
CREATE TABLE authors_16398b64 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_d12c36f9
CREATE TABLE publishers_d12c36f9 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_f5c8a1c4
CREATE TABLE books_f5c8a1c4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    publisher INTEGER,
    isbn VARCHAR(13) NOT NULL UNIQUE,
    price INTEGER NOT NULL DEFAULT 0,
    published_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_details_f7f222b0
CREATE TABLE book_details_f7f222b0 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_3ac27544
CREATE TABLE categories_3ac27544 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_91d36ff6
CREATE TABLE book_categories_91d36ff6 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_91d36ff6
DROP TABLE IF EXISTS book_categories_91d36ff6;

-- Drop table: categories_3ac27544
DROP TABLE IF EXISTS categories_3ac27544;

-- Drop table: book_details_f7f222b0
DROP TABLE IF EXISTS book_details_f7f222b0;

-- Drop table: books_f5c8a1c4
DROP TABLE IF EXISTS books_f5c8a1c4;

-- Drop table: publishers_d12c36f9
DROP TABLE IF EXISTS publishers_d12c36f9;

-- Drop table: authors_16398b64
DROP TABLE IF EXISTS authors_16398b64;
""",
        description="test_advanced_relationships_c2519235",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
