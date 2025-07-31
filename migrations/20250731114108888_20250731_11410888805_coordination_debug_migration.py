"""
Migration: 20250731_11410888805_coordination_debug_migration

Coordination debug migration

Generated on: 2025-07-31T06:11:08.888081
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="b7f74b2c-2f78-4719-984c-95e3e0e59f38",
        name="20250731_11410888805_coordination_debug_migration",
        version="20250731114108888",
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
        id="b7f74b2c-2f78-4719-984c-95e3e0e59f38",
        name="20250731_11410888805_coordination_debug_migration",
        version="20250731114108888",
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
