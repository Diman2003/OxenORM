"""
Migration: 20250731_11332125121_summary_migration_with_all_fixes

Summary migration with all fixes

Generated on: 2025-07-31T06:03:21.251244
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="f2d76ebe-1f8f-40f0-9fef-a1360a8af28a",
        name="20250731_11332125121_summary_migration_with_all_fixes",
        version="20250731113321251",
        up_sql="""-- Create table: summary_users
CREATE TABLE summary_users (
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    age INTEGER NOT NULL,
    height REAL NOT NULL,
    salary DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    birth_date DATE NOT NULL,
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: summary_users
DROP TABLE IF EXISTS summary_users;
""",
        description="Summary migration with all fixes",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="f2d76ebe-1f8f-40f0-9fef-a1360a8af28a",
        name="20250731_11332125121_summary_migration_with_all_fixes",
        version="20250731113321251",
        up_sql="""-- Create table: summary_users
CREATE TABLE summary_users (
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    age INTEGER NOT NULL,
    height REAL NOT NULL,
    salary DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    birth_date DATE NOT NULL,
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: summary_users
DROP TABLE IF EXISTS summary_users;
""",
        description="Summary migration with all fixes",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
