"""
Migration: 20250730_21491751373_basic_migration_with_simple_models

Basic migration with simple models

Generated on: 2025-07-30T16:19:17.513754
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="472e0fdd-3dce-4c55-8341-e8f915871985",
        name="20250730_21491751373_basic_migration_with_simple_models",
        version="20250730214917513",
        up_sql="""-- Create table: simpleuser
CREATE TABLE simpleuser (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simpleproduct
CREATE TABLE simpleproduct (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simpleproduct
DROP TABLE IF EXISTS simpleproduct;

-- Drop table: simpleuser
DROP TABLE IF EXISTS simpleuser;
""",
        description="Basic migration with simple models",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="472e0fdd-3dce-4c55-8341-e8f915871985",
        name="20250730_21491751373_basic_migration_with_simple_models",
        version="20250730214917513",
        up_sql="""-- Create table: simpleuser
CREATE TABLE simpleuser (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simpleproduct
CREATE TABLE simpleproduct (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simpleproduct
DROP TABLE IF EXISTS simpleproduct;

-- Drop table: simpleuser
DROP TABLE IF EXISTS simpleuser;
""",
        description="Basic migration with simple models",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
