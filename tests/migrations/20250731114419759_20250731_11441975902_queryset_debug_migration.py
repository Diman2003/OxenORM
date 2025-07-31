"""
Migration: 20250731_11441975902_queryset_debug_migration

QuerySet debug migration

Generated on: 2025-07-31T06:14:19.759048
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="6570dcbb-2fec-4535-98ae-4a3fc8cb0229",
        name="20250731_11441975902_queryset_debug_migration",
        version="20250731114419759",
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
        id="6570dcbb-2fec-4535-98ae-4a3fc8cb0229",
        name="20250731_11441975902_queryset_debug_migration",
        version="20250731114419759",
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
