"""
Migration: 20250731_11251565408_debug_migration

Debug migration

Generated on: 2025-07-31T05:55:15.654110
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="8d155976-54c9-42c6-ba5f-e211f92a82c8",
        name="20250731_11251565408_debug_migration",
        version="20250731112515654",
        up_sql="""-- Create table: debug_users
CREATE TABLE debug_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: debug_users
DROP TABLE IF EXISTS debug_users;
""",
        description="Debug migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="8d155976-54c9-42c6-ba5f-e211f92a82c8",
        name="20250731_11251565408_debug_migration",
        version="20250731112515654",
        up_sql="""-- Create table: debug_users
CREATE TABLE debug_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: debug_users
DROP TABLE IF EXISTS debug_users;
""",
        description="Debug migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
