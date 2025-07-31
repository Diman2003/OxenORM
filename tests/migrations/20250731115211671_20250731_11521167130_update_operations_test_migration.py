"""
Migration: 20250731_11521167130_update_operations_test_migration

Update Operations test migration

Generated on: 2025-07-31T06:22:11.671326
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="17f4f779-3c29-4bcc-88ee-c93398caa0f2",
        name="20250731_11521167130_update_operations_test_migration",
        version="20250731115211671",
        up_sql="""-- Create table: update_test_users
CREATE TABLE update_test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    email VARCHAR(255) NOT NULL UNIQUE,
    salary REAL,
    score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: update_test_users
DROP TABLE IF EXISTS update_test_users;
""",
        description="Update Operations test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="17f4f779-3c29-4bcc-88ee-c93398caa0f2",
        name="20250731_11521167130_update_operations_test_migration",
        version="20250731115211671",
        up_sql="""-- Create table: update_test_users
CREATE TABLE update_test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    email VARCHAR(255) NOT NULL UNIQUE,
    salary REAL,
    score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: update_test_users
DROP TABLE IF EXISTS update_test_users;
""",
        description="Update Operations test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
