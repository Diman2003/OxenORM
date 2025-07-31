"""
Migration: 20250731_15333792758_test_migration_debug

test_migration_debug

Generated on: 2025-07-31T10:03:37.927615
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="fd598402-38fa-464d-ab94-764ea913dc77",
        name="20250731_15333792758_test_migration_debug",
        version="20250731153337927",
        up_sql="""-- Create table: test_tags_debug
CREATE TABLE test_tags_debug (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT "#000000",
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
        id="fd598402-38fa-464d-ab94-764ea913dc77",
        name="20250731_15333792758_test_migration_debug",
        version="20250731153337927",
        up_sql="""-- Create table: test_tags_debug
CREATE TABLE test_tags_debug (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT "#000000",
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
