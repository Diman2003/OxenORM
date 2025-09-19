"""
Migration: 20250916_14275497749_coordination_debug_migration

Coordination debug migration

Generated on: 2025-09-16T08:57:54.977540
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="bcef4ab7-e0e7-41e4-8baa-0643bb0a390a",
        name="20250916_14275497749_coordination_debug_migration",
        version="20250916142754977",
        up_sql="""-- Create table: coordination_users
CREATE TABLE coordination_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: coordination_users
DROP TABLE IF EXISTS coordination_users;
""",
        description="Coordination debug migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="bcef4ab7-e0e7-41e4-8baa-0643bb0a390a",
        name="20250916_14275497749_coordination_debug_migration",
        version="20250916142754977",
        up_sql="""-- Create table: coordination_users
CREATE TABLE coordination_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: coordination_users
DROP TABLE IF EXISTS coordination_users;
""",
        description="Coordination debug migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
