"""
Migration: 20250730_21472564785_test_migration_for_rollback

Test migration for rollback

Generated on: 2025-07-30T16:17:25.647880
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="235cf3a1-6985-4d66-b11d-0f4dc72b94fb",
        name="20250730_21472564785_test_migration_for_rollback",
        version="20250730214725647",
        up_sql="""-- Create table: testuser
CREATE TABLE testuser (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: testproduct
CREATE TABLE testproduct (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: testproduct
DROP TABLE IF EXISTS testproduct;

-- Drop table: testuser
DROP TABLE IF EXISTS testuser;
""",
        description="Test migration for rollback",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="235cf3a1-6985-4d66-b11d-0f4dc72b94fb",
        name="20250730_21472564785_test_migration_for_rollback",
        version="20250730214725647",
        up_sql="""-- Create table: testuser
CREATE TABLE testuser (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: testproduct
CREATE TABLE testproduct (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: testproduct
DROP TABLE IF EXISTS testproduct;

-- Drop table: testuser
DROP TABLE IF EXISTS testuser;
""",
        description="Test migration for rollback",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
