"""
Migration: 20250731_11463014863_fresh_queryset_test_migration

Fresh QuerySet test migration

Generated on: 2025-07-31T06:16:30.148674
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="ee59827e-1a58-43cd-8cad-4477d58244f2",
        name="20250731_11463014863_fresh_queryset_test_migration",
        version="20250731114630148",
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
        id="ee59827e-1a58-43cd-8cad-4477d58244f2",
        name="20250731_11463014863_fresh_queryset_test_migration",
        version="20250731114630148",
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
