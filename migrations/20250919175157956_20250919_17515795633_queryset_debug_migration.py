"""
Migration: 20250919_17515795633_queryset_debug_migration

QuerySet debug migration

Generated on: 2025-09-19T12:21:57.956361
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="e73dac2e-c1e8-49b2-87c4-b4cd23081aca",
        name="20250919_17515795633_queryset_debug_migration",
        version="20250919175157956",
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
        id="e73dac2e-c1e8-49b2-87c4-b4cd23081aca",
        name="20250919_17515795633_queryset_debug_migration",
        version="20250919175157956",
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
