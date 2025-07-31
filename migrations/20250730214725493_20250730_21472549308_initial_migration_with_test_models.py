"""
Migration: 20250730_21472549308_initial_migration_with_test_models

Initial migration with test models

Generated on: 2025-07-30T16:17:25.493105
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="320f8a81-efc1-4dec-8150-ac01d9d3057d",
        name="20250730_21472549308_initial_migration_with_test_models",
        version="20250730214725493",
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
        description="Initial migration with test models",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="320f8a81-efc1-4dec-8150-ac01d9d3057d",
        name="20250730_21472549308_initial_migration_with_test_models",
        version="20250730214725493",
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
        description="Initial migration with test models",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
