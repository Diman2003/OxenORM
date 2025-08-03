"""
Migration: 20250803_21483865439_test_advanced_relationships_d8de1902

test_advanced_relationships_d8de1902

Generated on: 2025-08-03T16:18:38.654417
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="f5cf989a-33d5-4848-9cbc-af1dcc3b6ee6",
        name="20250803_21483865439_test_advanced_relationships_d8de1902",
        version="20250803214838654",
        up_sql="""-- Create table: authors_4e8e4bde
CREATE TABLE authors_4e8e4bde (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_68959f16
CREATE TABLE publishers_68959f16 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_4cb55059
CREATE TABLE books_4cb55059 (
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

-- Create table: book_details_1df6f00a
CREATE TABLE book_details_1df6f00a (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_83c51cab
CREATE TABLE categories_83c51cab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_c7edf23d
CREATE TABLE book_categories_c7edf23d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_c7edf23d
DROP TABLE IF EXISTS book_categories_c7edf23d;

-- Drop table: categories_83c51cab
DROP TABLE IF EXISTS categories_83c51cab;

-- Drop table: book_details_1df6f00a
DROP TABLE IF EXISTS book_details_1df6f00a;

-- Drop table: books_4cb55059
DROP TABLE IF EXISTS books_4cb55059;

-- Drop table: publishers_68959f16
DROP TABLE IF EXISTS publishers_68959f16;

-- Drop table: authors_4e8e4bde
DROP TABLE IF EXISTS authors_4e8e4bde;
""",
        description="test_advanced_relationships_d8de1902",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="f5cf989a-33d5-4848-9cbc-af1dcc3b6ee6",
        name="20250803_21483865439_test_advanced_relationships_d8de1902",
        version="20250803214838654",
        up_sql="""-- Create table: authors_4e8e4bde
CREATE TABLE authors_4e8e4bde (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_68959f16
CREATE TABLE publishers_68959f16 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_4cb55059
CREATE TABLE books_4cb55059 (
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

-- Create table: book_details_1df6f00a
CREATE TABLE book_details_1df6f00a (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_83c51cab
CREATE TABLE categories_83c51cab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_c7edf23d
CREATE TABLE book_categories_c7edf23d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_c7edf23d
DROP TABLE IF EXISTS book_categories_c7edf23d;

-- Drop table: categories_83c51cab
DROP TABLE IF EXISTS categories_83c51cab;

-- Drop table: book_details_1df6f00a
DROP TABLE IF EXISTS book_details_1df6f00a;

-- Drop table: books_4cb55059
DROP TABLE IF EXISTS books_4cb55059;

-- Drop table: publishers_68959f16
DROP TABLE IF EXISTS publishers_68959f16;

-- Drop table: authors_4e8e4bde
DROP TABLE IF EXISTS authors_4e8e4bde;
""",
        description="test_advanced_relationships_d8de1902",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
