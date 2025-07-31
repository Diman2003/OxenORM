"""
Migration: 20250730_21491756162_basic_migration_with_simple_models

Basic migration with simple models

Generated on: 2025-07-30T16:19:17.561652
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="efbe5a5f-10cc-4dfd-8072-bbf58148fc82",
        name="20250730_21491756162_basic_migration_with_simple_models",
        version="20250730214917561",
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
        id="efbe5a5f-10cc-4dfd-8072-bbf58148fc82",
        name="20250730_21491756162_basic_migration_with_simple_models",
        version="20250730214917561",
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
