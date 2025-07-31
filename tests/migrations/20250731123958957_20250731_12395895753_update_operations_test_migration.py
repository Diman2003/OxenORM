"""
Migration: 20250731_12395895753_update_operations_test_migration

Update Operations test migration

Generated on: 2025-07-31T07:09:58.957588
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="493be52f-dbf1-4b67-82ab-cc439e29fe90",
        name="20250731_12395895753_update_operations_test_migration",
        version="20250731123958957",
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
        id="493be52f-dbf1-4b67-82ab-cc439e29fe90",
        name="20250731_12395895753_update_operations_test_migration",
        version="20250731123958957",
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
