"""
Migration: 20250803_21474170569_test_advanced_relationships_9730b9ee

test_advanced_relationships_9730b9ee

Generated on: 2025-08-03T16:17:41.705718
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="0468e041-82cb-4217-8547-e2b0cd337251",
        name="20250803_21474170569_test_advanced_relationships_9730b9ee",
        version="20250803214741705",
        up_sql="""-- Create table: authors_4a1f32c9
CREATE TABLE authors_4a1f32c9 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_f2d8fb47
CREATE TABLE publishers_f2d8fb47 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_de468060
CREATE TABLE books_de468060 (
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

-- Create table: book_details_2f6d82c7
CREATE TABLE book_details_2f6d82c7 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_fc0c1166
CREATE TABLE categories_fc0c1166 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_4af3ccdc
CREATE TABLE book_categories_4af3ccdc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_4af3ccdc
DROP TABLE IF EXISTS book_categories_4af3ccdc;

-- Drop table: categories_fc0c1166
DROP TABLE IF EXISTS categories_fc0c1166;

-- Drop table: book_details_2f6d82c7
DROP TABLE IF EXISTS book_details_2f6d82c7;

-- Drop table: books_de468060
DROP TABLE IF EXISTS books_de468060;

-- Drop table: publishers_f2d8fb47
DROP TABLE IF EXISTS publishers_f2d8fb47;

-- Drop table: authors_4a1f32c9
DROP TABLE IF EXISTS authors_4a1f32c9;
""",
        description="test_advanced_relationships_9730b9ee",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="0468e041-82cb-4217-8547-e2b0cd337251",
        name="20250803_21474170569_test_advanced_relationships_9730b9ee",
        version="20250803214741705",
        up_sql="""-- Create table: authors_4a1f32c9
CREATE TABLE authors_4a1f32c9 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_f2d8fb47
CREATE TABLE publishers_f2d8fb47 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_de468060
CREATE TABLE books_de468060 (
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

-- Create table: book_details_2f6d82c7
CREATE TABLE book_details_2f6d82c7 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_fc0c1166
CREATE TABLE categories_fc0c1166 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_4af3ccdc
CREATE TABLE book_categories_4af3ccdc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_4af3ccdc
DROP TABLE IF EXISTS book_categories_4af3ccdc;

-- Drop table: categories_fc0c1166
DROP TABLE IF EXISTS categories_fc0c1166;

-- Drop table: book_details_2f6d82c7
DROP TABLE IF EXISTS book_details_2f6d82c7;

-- Drop table: books_de468060
DROP TABLE IF EXISTS books_de468060;

-- Drop table: publishers_f2d8fb47
DROP TABLE IF EXISTS publishers_f2d8fb47;

-- Drop table: authors_4a1f32c9
DROP TABLE IF EXISTS authors_4a1f32c9;
""",
        description="test_advanced_relationships_9730b9ee",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
