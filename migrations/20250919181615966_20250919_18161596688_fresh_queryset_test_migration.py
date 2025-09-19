"""
Migration: 20250919_18161596688_fresh_queryset_test_migration

Fresh QuerySet test migration

Generated on: 2025-09-19T12:46:15.966912
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="654093a5-6432-49c7-9d8f-4be885f06980",
        name="20250919_18161596688_fresh_queryset_test_migration",
        version="20250919181615966",
        up_sql="""-- Create table: fresh_test_users
CREATE TABLE fresh_test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: fresh_test_users
DROP TABLE IF EXISTS fresh_test_users;
""",
        description="Fresh QuerySet test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="654093a5-6432-49c7-9d8f-4be885f06980",
        name="20250919_18161596688_fresh_queryset_test_migration",
        version="20250919181615966",
        up_sql="""-- Create table: fresh_test_users
CREATE TABLE fresh_test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: fresh_test_users
DROP TABLE IF EXISTS fresh_test_users;
""",
        description="Fresh QuerySet test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
