"""
Migration: 20250803_21465382949_test_advanced_relationships_749fa9e8

test_advanced_relationships_749fa9e8

Generated on: 2025-08-03T16:16:53.829532
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="902c4603-5a31-45e5-a430-7af8d312c5a7",
        name="20250803_21465382949_test_advanced_relationships_749fa9e8",
        version="20250803214653829",
        up_sql="""-- Create table: authors_03f7d34c
CREATE TABLE authors_03f7d34c (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_a80e1f9c
CREATE TABLE publishers_a80e1f9c (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_0e062839
CREATE TABLE books_0e062839 (
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

-- Create table: book_details_991eec34
CREATE TABLE book_details_991eec34 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_7d5667a4
CREATE TABLE categories_7d5667a4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_683ed5ef
CREATE TABLE book_categories_683ed5ef (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_683ed5ef
DROP TABLE IF EXISTS book_categories_683ed5ef;

-- Drop table: categories_7d5667a4
DROP TABLE IF EXISTS categories_7d5667a4;

-- Drop table: book_details_991eec34
DROP TABLE IF EXISTS book_details_991eec34;

-- Drop table: books_0e062839
DROP TABLE IF EXISTS books_0e062839;

-- Drop table: publishers_a80e1f9c
DROP TABLE IF EXISTS publishers_a80e1f9c;

-- Drop table: authors_03f7d34c
DROP TABLE IF EXISTS authors_03f7d34c;
""",
        description="test_advanced_relationships_749fa9e8",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="902c4603-5a31-45e5-a430-7af8d312c5a7",
        name="20250803_21465382949_test_advanced_relationships_749fa9e8",
        version="20250803214653829",
        up_sql="""-- Create table: authors_03f7d34c
CREATE TABLE authors_03f7d34c (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_a80e1f9c
CREATE TABLE publishers_a80e1f9c (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_0e062839
CREATE TABLE books_0e062839 (
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

-- Create table: book_details_991eec34
CREATE TABLE book_details_991eec34 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_7d5667a4
CREATE TABLE categories_7d5667a4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_683ed5ef
CREATE TABLE book_categories_683ed5ef (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_683ed5ef
DROP TABLE IF EXISTS book_categories_683ed5ef;

-- Drop table: categories_7d5667a4
DROP TABLE IF EXISTS categories_7d5667a4;

-- Drop table: book_details_991eec34
DROP TABLE IF EXISTS book_details_991eec34;

-- Drop table: books_0e062839
DROP TABLE IF EXISTS books_0e062839;

-- Drop table: publishers_a80e1f9c
DROP TABLE IF EXISTS publishers_a80e1f9c;

-- Drop table: authors_03f7d34c
DROP TABLE IF EXISTS authors_03f7d34c;
""",
        description="test_advanced_relationships_749fa9e8",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
