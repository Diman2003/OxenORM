"""
Migration: 20250803_21414926873_test_debug_schema_2dfcb256

test_debug_schema_2dfcb256

Generated on: 2025-08-03T16:11:49.268760
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="613920cb-21c7-422b-885f-3ded80b2c67d",
        name="20250803_21414926873_test_debug_schema_2dfcb256",
        version="20250803214149268",
        up_sql="""-- Create table: authors_4b6446b4
CREATE TABLE authors_4b6446b4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_2ff4ca9a
CREATE TABLE books_2ff4ca9a (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: books_2ff4ca9a
DROP TABLE IF EXISTS books_2ff4ca9a;

-- Drop table: authors_4b6446b4
DROP TABLE IF EXISTS authors_4b6446b4;
""",
        description="test_debug_schema_2dfcb256",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="613920cb-21c7-422b-885f-3ded80b2c67d",
        name="20250803_21414926873_test_debug_schema_2dfcb256",
        version="20250803214149268",
        up_sql="""-- Create table: authors_4b6446b4
CREATE TABLE authors_4b6446b4 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: books_2ff4ca9a
CREATE TABLE books_2ff4ca9a (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    author INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: books_2ff4ca9a
DROP TABLE IF EXISTS books_2ff4ca9a;

-- Drop table: authors_4b6446b4
DROP TABLE IF EXISTS authors_4b6446b4;
""",
        description="test_debug_schema_2dfcb256",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
