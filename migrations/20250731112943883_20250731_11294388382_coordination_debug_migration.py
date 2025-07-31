"""
Migration: 20250731_11294388382_coordination_debug_migration

Coordination debug migration

Generated on: 2025-07-31T05:59:43.883857
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="f71a9738-8679-4894-b9d9-041c6f060646",
        name="20250731_11294388382_coordination_debug_migration",
        version="20250731112943883",
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
        id="f71a9738-8679-4894-b9d9-041c6f060646",
        name="20250731_11294388382_coordination_debug_migration",
        version="20250731112943883",
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
