"""
Migration: 20250731_13254450844_test_simple_relations

test_simple_relations

Generated on: 2025-07-31T07:55:44.508570
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="811d386b-2c65-46f3-afd8-4afb238b7d29",
        name="20250731_13254450844_test_simple_relations",
        version="20250731132544508",
        up_sql="""-- Create table: simple_authors
CREATE TABLE simple_authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_books
CREATE TABLE simple_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    price INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simple_books
DROP TABLE IF EXISTS simple_books;

-- Drop table: simple_authors
DROP TABLE IF EXISTS simple_authors;
""",
        description="test_simple_relations",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="811d386b-2c65-46f3-afd8-4afb238b7d29",
        name="20250731_13254450844_test_simple_relations",
        version="20250731132544508",
        up_sql="""-- Create table: simple_authors
CREATE TABLE simple_authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_books
CREATE TABLE simple_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    price INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simple_books
DROP TABLE IF EXISTS simple_books;

-- Drop table: simple_authors
DROP TABLE IF EXISTS simple_authors;
""",
        description="test_simple_relations",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
