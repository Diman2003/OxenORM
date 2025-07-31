"""
Migration: 20250731_12340025257_update_operations_test_migration

Update Operations test migration

Generated on: 2025-07-31T07:04:00.252603
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="b5ce5b92-ff8e-42d9-bc18-67172877c3c3",
        name="20250731_12340025257_update_operations_test_migration",
        version="20250731123400252",
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
        id="b5ce5b92-ff8e-42d9-bc18-67172877c3c3",
        name="20250731_12340025257_update_operations_test_migration",
        version="20250731123400252",
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
