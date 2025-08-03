"""
Migration: 20250803_20550750637_test_update_operations

test_update_operations

Generated on: 2025-08-03T15:25:07.506397
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="f332eb85-768f-44ea-8c82-1270aee241f3",
        name="20250803_20550750637_test_update_operations",
        version="20250803205507506",
        up_sql="""-- Create table: test_users
CREATE TABLE test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_products
CREATE TABLE test_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    description VARCHAR(500),
    is_available BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: test_products
DROP TABLE IF EXISTS test_products;

-- Drop table: test_users
DROP TABLE IF EXISTS test_users;
""",
        description="test_update_operations",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="f332eb85-768f-44ea-8c82-1270aee241f3",
        name="20250803_20550750637_test_update_operations",
        version="20250803205507506",
        up_sql="""-- Create table: test_users
CREATE TABLE test_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: test_products
CREATE TABLE test_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    description VARCHAR(500),
    is_available BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: test_products
DROP TABLE IF EXISTS test_products;

-- Drop table: test_users
DROP TABLE IF EXISTS test_users;
""",
        description="test_update_operations",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
