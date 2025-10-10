"""
Migration: 20250919_23450821266_summary_migration_with_all_fixes

Summary migration with all fixes

Generated on: 2025-09-19T18:15:08.212699
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="318863f0-e42a-4535-82cb-163cbe0e0399",
        name="20250919_23450821266_summary_migration_with_all_fixes",
        version="20250919234508212",
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
        id="318863f0-e42a-4535-82cb-163cbe0e0399",
        name="20250919_23450821266_summary_migration_with_all_fixes",
        version="20250919234508212",
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
