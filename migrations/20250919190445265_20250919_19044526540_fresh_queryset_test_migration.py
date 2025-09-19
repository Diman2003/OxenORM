"""
Migration: 20250919_19044526540_fresh_queryset_test_migration

Fresh QuerySet test migration

Generated on: 2025-09-19T13:34:45.265432
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="308d9e62-539f-4ed1-afc7-0e1cc080cd68",
        name="20250919_19044526540_fresh_queryset_test_migration",
        version="20250919190445265",
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
        id="308d9e62-539f-4ed1-afc7-0e1cc080cd68",
        name="20250919_19044526540_fresh_queryset_test_migration",
        version="20250919190445265",
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
