"""
Migration: 20250919_18161574961_queryset_debug_migration

QuerySet debug migration

Generated on: 2025-09-19T12:46:15.749655
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="e04d7b94-9886-4cc3-9729-91c60939bfa5",
        name="20250919_18161574961_queryset_debug_migration",
        version="20250919181615749",
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
        id="e04d7b94-9886-4cc3-9729-91c60939bfa5",
        name="20250919_18161574961_queryset_debug_migration",
        version="20250919181615749",
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
