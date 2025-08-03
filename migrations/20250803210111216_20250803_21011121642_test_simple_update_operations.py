"""
Migration: 20250803_21011121642_test_simple_update_operations

test_simple_update_operations

Generated on: 2025-08-03T15:31:11.216455
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="dba4ceee-902f-4665-86ee-0e26328e382f",
        name="20250803_21011121642_test_simple_update_operations",
        version="20250803210111216",
        up_sql="""-- Create table: simple_users
CREATE TABLE simple_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_products
CREATE TABLE simple_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    description VARCHAR(500),
    is_available BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simple_products
DROP TABLE IF EXISTS simple_products;

-- Drop table: simple_users
DROP TABLE IF EXISTS simple_users;
""",
        description="test_simple_update_operations",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="dba4ceee-902f-4665-86ee-0e26328e382f",
        name="20250803_21011121642_test_simple_update_operations",
        version="20250803210111216",
        up_sql="""-- Create table: simple_users
CREATE TABLE simple_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_products
CREATE TABLE simple_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    description VARCHAR(500),
    is_available BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simple_products
DROP TABLE IF EXISTS simple_products;

-- Drop table: simple_users
DROP TABLE IF EXISTS simple_users;
""",
        description="test_simple_update_operations",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
