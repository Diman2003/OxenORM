"""
Migration: 20250803_21390483494_test_advanced_relationships_715f71b0

test_advanced_relationships_715f71b0

Generated on: 2025-08-03T16:09:04.834974
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="88eb4389-ed85-436f-a526-7cb605057e2b",
        name="20250803_21390483494_test_advanced_relationships_715f71b0",
        version="20250803213904834",
        up_sql="""-- Create table: authors_e93e5d7e
CREATE TABLE authors_e93e5d7e (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_bd51aab7
CREATE TABLE publishers_bd51aab7 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_df2bed76
CREATE TABLE books_df2bed76 (
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

-- Create table: book_details_1ee894a8
CREATE TABLE book_details_1ee894a8 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_a4f1fb5d
CREATE TABLE categories_a4f1fb5d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_cead2370
CREATE TABLE book_categories_cead2370 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_cead2370
DROP TABLE IF EXISTS book_categories_cead2370;

-- Drop table: categories_a4f1fb5d
DROP TABLE IF EXISTS categories_a4f1fb5d;

-- Drop table: book_details_1ee894a8
DROP TABLE IF EXISTS book_details_1ee894a8;

-- Drop table: books_df2bed76
DROP TABLE IF EXISTS books_df2bed76;

-- Drop table: publishers_bd51aab7
DROP TABLE IF EXISTS publishers_bd51aab7;

-- Drop table: authors_e93e5d7e
DROP TABLE IF EXISTS authors_e93e5d7e;
""",
        description="test_advanced_relationships_715f71b0",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="88eb4389-ed85-436f-a526-7cb605057e2b",
        name="20250803_21390483494_test_advanced_relationships_715f71b0",
        version="20250803213904834",
        up_sql="""-- Create table: authors_e93e5d7e
CREATE TABLE authors_e93e5d7e (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: publishers_bd51aab7
CREATE TABLE publishers_bd51aab7 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_df2bed76
CREATE TABLE books_df2bed76 (
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

-- Create table: book_details_1ee894a8
CREATE TABLE book_details_1ee894a8 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER UNIQUE,
    pages INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(50) NOT NULL DEFAULT "English",
    format VARCHAR(50) NOT NULL DEFAULT "Paperback",
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: categories_a4f1fb5d
CREATE TABLE categories_a4f1fb5d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: book_categories_cead2370
CREATE TABLE book_categories_cead2370 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book INTEGER,
    category INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: book_categories_cead2370
DROP TABLE IF EXISTS book_categories_cead2370;

-- Drop table: categories_a4f1fb5d
DROP TABLE IF EXISTS categories_a4f1fb5d;

-- Drop table: book_details_1ee894a8
DROP TABLE IF EXISTS book_details_1ee894a8;

-- Drop table: books_df2bed76
DROP TABLE IF EXISTS books_df2bed76;

-- Drop table: publishers_bd51aab7
DROP TABLE IF EXISTS publishers_bd51aab7;

-- Drop table: authors_e93e5d7e
DROP TABLE IF EXISTS authors_e93e5d7e;
""",
        description="test_advanced_relationships_715f71b0",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
