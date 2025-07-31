"""
Migration: 20250731_13310717308_test_simple_relations

test_simple_relations

Generated on: 2025-07-31T08:01:07.173142
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="81456b2f-3a0b-4626-8cf8-639c6e6b9de0",
        name="20250731_13310717308_test_simple_relations",
        version="20250731133107173",
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
        id="81456b2f-3a0b-4626-8cf8-639c6e6b9de0",
        name="20250731_13310717308_test_simple_relations",
        version="20250731133107173",
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
