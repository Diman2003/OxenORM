"""
Migration: 20250803_21402138122_test_advanced_relationships_9da0eed1

test_advanced_relationships_9da0eed1

Generated on: 2025-08-03T16:10:21.381256
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="e7945c74-d1bb-456b-91f2-5ceb458c990e",
        name="20250803_21402138122_test_advanced_relationships_9da0eed1",
        version="20250803214021381",
        up_sql="""-- Create table: authors_baf58053
CREATE TABLE authors_baf58053 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_5025c18f
CREATE TABLE publishers_5025c18f (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_41e738e0
CREATE TABLE books_41e738e0 (
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

-- Create table: book_details_0eb837d7
CREATE TABLE book_details_0eb837d7 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_cd433d31
CREATE TABLE categories_cd433d31 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_b31b28f4
CREATE TABLE book_categories_b31b28f4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_b31b28f4
DROP TABLE IF EXISTS book_categories_b31b28f4;

-- Drop table: categories_cd433d31
DROP TABLE IF EXISTS categories_cd433d31;

-- Drop table: book_details_0eb837d7
DROP TABLE IF EXISTS book_details_0eb837d7;

-- Drop table: books_41e738e0
DROP TABLE IF EXISTS books_41e738e0;

-- Drop table: publishers_5025c18f
DROP TABLE IF EXISTS publishers_5025c18f;

-- Drop table: authors_baf58053
DROP TABLE IF EXISTS authors_baf58053;
""",
        description="test_advanced_relationships_9da0eed1",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="e7945c74-d1bb-456b-91f2-5ceb458c990e",
        name="20250803_21402138122_test_advanced_relationships_9da0eed1",
        version="20250803214021381",
        up_sql="""-- Create table: authors_baf58053
CREATE TABLE authors_baf58053 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_5025c18f
CREATE TABLE publishers_5025c18f (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_41e738e0
CREATE TABLE books_41e738e0 (
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

-- Create table: book_details_0eb837d7
CREATE TABLE book_details_0eb837d7 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_cd433d31
CREATE TABLE categories_cd433d31 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_b31b28f4
CREATE TABLE book_categories_b31b28f4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_b31b28f4
DROP TABLE IF EXISTS book_categories_b31b28f4;

-- Drop table: categories_cd433d31
DROP TABLE IF EXISTS categories_cd433d31;

-- Drop table: book_details_0eb837d7
DROP TABLE IF EXISTS book_details_0eb837d7;

-- Drop table: books_41e738e0
DROP TABLE IF EXISTS books_41e738e0;

-- Drop table: publishers_5025c18f
DROP TABLE IF EXISTS publishers_5025c18f;

-- Drop table: authors_baf58053
DROP TABLE IF EXISTS authors_baf58053;
""",
        description="test_advanced_relationships_9da0eed1",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
