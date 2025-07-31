"""
Migration: 20250731_11413265198_coordination_debug_migration

Coordination debug migration

Generated on: 2025-07-31T06:11:32.652013
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="d64a7055-73b0-4056-ab78-926fe07cd5f6",
        name="20250731_11413265198_coordination_debug_migration",
        version="20250731114132652",
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
        id="d64a7055-73b0-4056-ab78-926fe07cd5f6",
        name="20250731_11413265198_coordination_debug_migration",
        version="20250731114132652",
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
