"""
Migration: 20250803_21411730308_test_advanced_relationships_839dbc0f

test_advanced_relationships_839dbc0f

Generated on: 2025-08-03T16:11:17.303111
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="c69e6cf7-77cb-48c8-8691-10aeaae30498",
        name="20250803_21411730308_test_advanced_relationships_839dbc0f",
        version="20250803214117303",
        up_sql="""-- Create table: authors_666f2b49
CREATE TABLE authors_666f2b49 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_90d681b7
CREATE TABLE publishers_90d681b7 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_44533125
CREATE TABLE books_44533125 (
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

-- Create table: book_details_3cd5ffa9
CREATE TABLE book_details_3cd5ffa9 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_e92ebb95
CREATE TABLE categories_e92ebb95 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_daffbd5b
CREATE TABLE book_categories_daffbd5b (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_daffbd5b
DROP TABLE IF EXISTS book_categories_daffbd5b;

-- Drop table: categories_e92ebb95
DROP TABLE IF EXISTS categories_e92ebb95;

-- Drop table: book_details_3cd5ffa9
DROP TABLE IF EXISTS book_details_3cd5ffa9;

-- Drop table: books_44533125
DROP TABLE IF EXISTS books_44533125;

-- Drop table: publishers_90d681b7
DROP TABLE IF EXISTS publishers_90d681b7;

-- Drop table: authors_666f2b49
DROP TABLE IF EXISTS authors_666f2b49;
""",
        description="test_advanced_relationships_839dbc0f",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="c69e6cf7-77cb-48c8-8691-10aeaae30498",
        name="20250803_21411730308_test_advanced_relationships_839dbc0f",
        version="20250803214117303",
        up_sql="""-- Create table: authors_666f2b49
CREATE TABLE authors_666f2b49 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_90d681b7
CREATE TABLE publishers_90d681b7 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_44533125
CREATE TABLE books_44533125 (
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

-- Create table: book_details_3cd5ffa9
CREATE TABLE book_details_3cd5ffa9 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_e92ebb95
CREATE TABLE categories_e92ebb95 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_daffbd5b
CREATE TABLE book_categories_daffbd5b (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_daffbd5b
DROP TABLE IF EXISTS book_categories_daffbd5b;

-- Drop table: categories_e92ebb95
DROP TABLE IF EXISTS categories_e92ebb95;

-- Drop table: book_details_3cd5ffa9
DROP TABLE IF EXISTS book_details_3cd5ffa9;

-- Drop table: books_44533125
DROP TABLE IF EXISTS books_44533125;

-- Drop table: publishers_90d681b7
DROP TABLE IF EXISTS publishers_90d681b7;

-- Drop table: authors_666f2b49
DROP TABLE IF EXISTS authors_666f2b49;
""",
        description="test_advanced_relationships_839dbc0f",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
