"""
Migration: 20250731_11230017445_status_test_migration

Status test migration

Generated on: 2025-07-31T05:53:00.174483
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="a4c4a837-e413-47fe-9b3e-72c66a38cd2c",
        name="20250731_11230017445_status_test_migration",
        version="20250731112300174",
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
    user_id VARCHAR(255) NOT NULL UNIQUE,
    profile_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simple_users
DROP TABLE IF EXISTS simple_users;
""",
        description="Status test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="a4c4a837-e413-47fe-9b3e-72c66a38cd2c",
        name="20250731_11230017445_status_test_migration",
        version="20250731112300174",
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
    user_id VARCHAR(255) NOT NULL UNIQUE,
    profile_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simple_users
DROP TABLE IF EXISTS simple_users;
""",
        description="Status test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
