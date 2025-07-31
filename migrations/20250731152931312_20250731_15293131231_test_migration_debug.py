"""
Migration: 20250731_15293131231_test_migration_debug

test_migration_debug

Generated on: 2025-07-31T09:59:31.312347
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="4a1be0ae-2d97-44dd-9fc7-05e307d1eb06",
        name="20250731_15293131231_test_migration_debug",
        version="20250731152931312",
        up_sql="""-- Create table: test_tags_debug
CREATE TABLE test_tags_debug (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT '#000000',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: test_tags_debug
DROP TABLE IF EXISTS test_tags_debug;
""",
        description="test_migration_debug",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="4a1be0ae-2d97-44dd-9fc7-05e307d1eb06",
        name="20250731_15293131231_test_migration_debug",
        version="20250731152931312",
        up_sql="""-- Create table: test_tags_debug
CREATE TABLE test_tags_debug (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT '#000000',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: test_tags_debug
DROP TABLE IF EXISTS test_tags_debug;
""",
        description="test_migration_debug",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
