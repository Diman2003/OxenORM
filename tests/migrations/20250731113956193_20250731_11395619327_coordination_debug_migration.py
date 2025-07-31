"""
Migration: 20250731_11395619327_coordination_debug_migration

Coordination debug migration

Generated on: 2025-07-31T06:09:56.193299
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="3e9277bd-1334-4b59-a253-8a37535471d4",
        name="20250731_11395619327_coordination_debug_migration",
        version="20250731113956193",
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
        id="3e9277bd-1334-4b59-a253-8a37535471d4",
        name="20250731_11395619327_coordination_debug_migration",
        version="20250731113956193",
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
