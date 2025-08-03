"""
Migration: 20250803_21400050340_test_advanced_relationships_2cdccc3e

test_advanced_relationships_2cdccc3e

Generated on: 2025-08-03T16:10:00.503432
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="8dccbc95-d20b-4b60-bdd3-b4dd1c3c24e5",
        name="20250803_21400050340_test_advanced_relationships_2cdccc3e",
        version="20250803214000503",
        up_sql="""-- Create table: authors_c473b307
CREATE TABLE authors_c473b307 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_82db1650
CREATE TABLE publishers_82db1650 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_9785b0b4
CREATE TABLE books_9785b0b4 (
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

-- Create table: book_details_87768bd9
CREATE TABLE book_details_87768bd9 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_f43e3e16
CREATE TABLE categories_f43e3e16 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_2e373b87
CREATE TABLE book_categories_2e373b87 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_2e373b87
DROP TABLE IF EXISTS book_categories_2e373b87;

-- Drop table: categories_f43e3e16
DROP TABLE IF EXISTS categories_f43e3e16;

-- Drop table: book_details_87768bd9
DROP TABLE IF EXISTS book_details_87768bd9;

-- Drop table: books_9785b0b4
DROP TABLE IF EXISTS books_9785b0b4;

-- Drop table: publishers_82db1650
DROP TABLE IF EXISTS publishers_82db1650;

-- Drop table: authors_c473b307
DROP TABLE IF EXISTS authors_c473b307;
""",
        description="test_advanced_relationships_2cdccc3e",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="8dccbc95-d20b-4b60-bdd3-b4dd1c3c24e5",
        name="20250803_21400050340_test_advanced_relationships_2cdccc3e",
        version="20250803214000503",
        up_sql="""-- Create table: authors_c473b307
CREATE TABLE authors_c473b307 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_82db1650
CREATE TABLE publishers_82db1650 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_9785b0b4
CREATE TABLE books_9785b0b4 (
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

-- Create table: book_details_87768bd9
CREATE TABLE book_details_87768bd9 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_f43e3e16
CREATE TABLE categories_f43e3e16 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_2e373b87
CREATE TABLE book_categories_2e373b87 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_2e373b87
DROP TABLE IF EXISTS book_categories_2e373b87;

-- Drop table: categories_f43e3e16
DROP TABLE IF EXISTS categories_f43e3e16;

-- Drop table: book_details_87768bd9
DROP TABLE IF EXISTS book_details_87768bd9;

-- Drop table: books_9785b0b4
DROP TABLE IF EXISTS books_9785b0b4;

-- Drop table: publishers_82db1650
DROP TABLE IF EXISTS publishers_82db1650;

-- Drop table: authors_c473b307
DROP TABLE IF EXISTS authors_c473b307;
""",
        description="test_advanced_relationships_2cdccc3e",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
