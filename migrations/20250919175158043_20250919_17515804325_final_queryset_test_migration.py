"""
Migration: 20250919_17515804325_final_queryset_test_migration

Final QuerySet test migration

Generated on: 2025-09-19T12:21:58.043284
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="37b0e941-87d6-4f31-acc1-61e8eb1e801d",
        name="20250919_17515804325_final_queryset_test_migration",
        version="20250919175158043",
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
        id="37b0e941-87d6-4f31-acc1-61e8eb1e801d",
        name="20250919_17515804325_final_queryset_test_migration",
        version="20250919175158043",
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
