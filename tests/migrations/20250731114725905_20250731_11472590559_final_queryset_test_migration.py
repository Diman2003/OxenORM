"""
Migration: 20250731_11472590559_final_queryset_test_migration

Final QuerySet test migration

Generated on: 2025-07-31T06:17:25.905635
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="72e3bed0-a35e-43e0-8714-7efeaf6676cc",
        name="20250731_11472590559_final_queryset_test_migration",
        version="20250731114725905",
        up_sql="""-- Create table: final_test_users
CREATE TABLE final_test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: final_test_users
DROP TABLE IF EXISTS final_test_users;
""",
        description="Final QuerySet test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="72e3bed0-a35e-43e0-8714-7efeaf6676cc",
        name="20250731_11472590559_final_queryset_test_migration",
        version="20250731114725905",
        up_sql="""-- Create table: final_test_users
CREATE TABLE final_test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: final_test_users
DROP TABLE IF EXISTS final_test_users;
""",
        description="Final QuerySet test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
