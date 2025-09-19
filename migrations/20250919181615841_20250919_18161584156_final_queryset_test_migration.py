"""
Migration: 20250919_18161584156_final_queryset_test_migration

Final QuerySet test migration

Generated on: 2025-09-19T12:46:15.841591
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="7b25d3ea-36e0-4bdd-8343-e065e1204aae",
        name="20250919_18161584156_final_queryset_test_migration",
        version="20250919181615841",
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
        id="7b25d3ea-36e0-4bdd-8343-e065e1204aae",
        name="20250919_18161584156_final_queryset_test_migration",
        version="20250919181615841",
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
