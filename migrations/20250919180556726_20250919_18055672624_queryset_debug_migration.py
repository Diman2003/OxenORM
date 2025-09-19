"""
Migration: 20250919_18055672624_queryset_debug_migration

QuerySet debug migration

Generated on: 2025-09-19T12:35:56.726269
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="ca0745a6-7e29-4ce0-97b0-8d2686e379ff",
        name="20250919_18055672624_queryset_debug_migration",
        version="20250919180556726",
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
        id="ca0745a6-7e29-4ce0-97b0-8d2686e379ff",
        name="20250919_18055672624_queryset_debug_migration",
        version="20250919180556726",
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
