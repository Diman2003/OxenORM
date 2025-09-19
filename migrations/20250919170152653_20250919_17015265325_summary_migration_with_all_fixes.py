"""
Migration: 20250919_17015265325_summary_migration_with_all_fixes

Summary migration with all fixes

Generated on: 2025-09-19T11:31:52.653746
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="58d2ea1a-e816-4fc3-9b27-5dd9d6f96b77",
        name="20250919_17015265325_summary_migration_with_all_fixes",
        version="20250919170152653",
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
        id="58d2ea1a-e816-4fc3-9b27-5dd9d6f96b77",
        name="20250919_17015265325_summary_migration_with_all_fixes",
        version="20250919170152653",
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
