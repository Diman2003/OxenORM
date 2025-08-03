"""
Migration: 20250803_21393254379_test_advanced_relationships_f9c8acb2

test_advanced_relationships_f9c8acb2

Generated on: 2025-08-03T16:09:32.543816
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="cd23cfef-7fd2-44a2-b115-8ba2c14a3190",
        name="20250803_21393254379_test_advanced_relationships_f9c8acb2",
        version="20250803213932543",
        up_sql="""-- Create table: authors_0a69aa7f
CREATE TABLE authors_0a69aa7f (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_63ea5cb2
CREATE TABLE publishers_63ea5cb2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_720935c7
CREATE TABLE books_720935c7 (
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

-- Create table: book_details_99695569
CREATE TABLE book_details_99695569 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_f259aeab
CREATE TABLE categories_f259aeab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_1640f58d
CREATE TABLE book_categories_1640f58d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_1640f58d
DROP TABLE IF EXISTS book_categories_1640f58d;

-- Drop table: categories_f259aeab
DROP TABLE IF EXISTS categories_f259aeab;

-- Drop table: book_details_99695569
DROP TABLE IF EXISTS book_details_99695569;

-- Drop table: books_720935c7
DROP TABLE IF EXISTS books_720935c7;

-- Drop table: publishers_63ea5cb2
DROP TABLE IF EXISTS publishers_63ea5cb2;

-- Drop table: authors_0a69aa7f
DROP TABLE IF EXISTS authors_0a69aa7f;
""",
        description="test_advanced_relationships_f9c8acb2",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="cd23cfef-7fd2-44a2-b115-8ba2c14a3190",
        name="20250803_21393254379_test_advanced_relationships_f9c8acb2",
        version="20250803213932543",
        up_sql="""-- Create table: authors_0a69aa7f
CREATE TABLE authors_0a69aa7f (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_63ea5cb2
CREATE TABLE publishers_63ea5cb2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_720935c7
CREATE TABLE books_720935c7 (
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

-- Create table: book_details_99695569
CREATE TABLE book_details_99695569 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_f259aeab
CREATE TABLE categories_f259aeab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_1640f58d
CREATE TABLE book_categories_1640f58d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_1640f58d
DROP TABLE IF EXISTS book_categories_1640f58d;

-- Drop table: categories_f259aeab
DROP TABLE IF EXISTS categories_f259aeab;

-- Drop table: book_details_99695569
DROP TABLE IF EXISTS book_details_99695569;

-- Drop table: books_720935c7
DROP TABLE IF EXISTS books_720935c7;

-- Drop table: publishers_63ea5cb2
DROP TABLE IF EXISTS publishers_63ea5cb2;

-- Drop table: authors_0a69aa7f
DROP TABLE IF EXISTS authors_0a69aa7f;
""",
        description="test_advanced_relationships_f9c8acb2",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
