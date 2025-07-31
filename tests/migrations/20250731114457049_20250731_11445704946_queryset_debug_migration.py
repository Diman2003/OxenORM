"""
Migration: 20250731_11445704946_queryset_debug_migration

QuerySet debug migration

Generated on: 2025-07-31T06:14:57.049498
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="e546f83f-1b92-49ba-89d3-e26d5dde5ecc",
        name="20250731_11445704946_queryset_debug_migration",
        version="20250731114457049",
        up_sql="""-- Create table: query_test_users
CREATE TABLE query_test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: query_test_users
DROP TABLE IF EXISTS query_test_users;
""",
        description="QuerySet debug migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="e546f83f-1b92-49ba-89d3-e26d5dde5ecc",
        name="20250731_11445704946_queryset_debug_migration",
        version="20250731114457049",
        up_sql="""-- Create table: query_test_users
CREATE TABLE query_test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: query_test_users
DROP TABLE IF EXISTS query_test_users;
""",
        description="QuerySet debug migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
