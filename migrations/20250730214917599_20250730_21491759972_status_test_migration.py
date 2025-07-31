"""
Migration: 20250730_21491759972_status_test_migration

Status test migration

Generated on: 2025-07-30T16:19:17.599742
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="9c8b5a14-7b0f-4816-a863-8fead3bbf515",
        name="20250730_21491759972_status_test_migration",
        version="20250730214917599",
        up_sql="""-- Create table: simpleuser
CREATE TABLE simpleuser (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simpleuser
DROP TABLE IF EXISTS simpleuser;
""",
        description="Status test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="9c8b5a14-7b0f-4816-a863-8fead3bbf515",
        name="20250730_21491759972_status_test_migration",
        version="20250730214917599",
        up_sql="""-- Create table: simpleuser
CREATE TABLE simpleuser (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simpleuser
DROP TABLE IF EXISTS simpleuser;
""",
        description="Status test migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
