"""
Migration: 20250731_11392005802_simple_coordination_migration

Simple coordination migration

Generated on: 2025-07-31T06:09:20.058048
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="9f38c37c-2651-4435-8019-52892b33e67f",
        name="20250731_11392005802_simple_coordination_migration",
        version="20250731113920058",
        up_sql="""-- Create table: simple_users
CREATE TABLE simple_users (
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
        down_sql="""-- Drop table: simple_users
DROP TABLE IF EXISTS simple_users;
""",
        description="Simple coordination migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="9f38c37c-2651-4435-8019-52892b33e67f",
        name="20250731_11392005802_simple_coordination_migration",
        version="20250731113920058",
        up_sql="""-- Create table: simple_users
CREATE TABLE simple_users (
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
        down_sql="""-- Drop table: simple_users
DROP TABLE IF EXISTS simple_users;
""",
        description="Simple coordination migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
