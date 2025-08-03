"""
Migration: 20250803_21562466027_test_query_optimization_3a23cf31

test_query_optimization_3a23cf31

Generated on: 2025-08-03T16:26:24.660306
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="7f96d87a-b906-4e05-8545-226d4d74ebb4",
        name="20250803_21562466027_test_query_optimization_3a23cf31",
        version="20250803215624660",
        up_sql="""-- Create table: users_d388e915
CREATE TABLE users_d388e915 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: products_1161b936
CREATE TABLE products_1161b936 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT True,
    user INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: orders_33c3ebc3
CREATE TABLE orders_33c3ebc3 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    total_amount INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT "pending",
    user INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: orders_33c3ebc3
DROP TABLE IF EXISTS orders_33c3ebc3;

-- Drop table: products_1161b936
DROP TABLE IF EXISTS products_1161b936;

-- Drop table: users_d388e915
DROP TABLE IF EXISTS users_d388e915;
""",
        description="test_query_optimization_3a23cf31",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="7f96d87a-b906-4e05-8545-226d4d74ebb4",
        name="20250803_21562466027_test_query_optimization_3a23cf31",
        version="20250803215624660",
        up_sql="""-- Create table: users_d388e915
CREATE TABLE users_d388e915 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: products_1161b936
CREATE TABLE products_1161b936 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT True,
    user INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: orders_33c3ebc3
CREATE TABLE orders_33c3ebc3 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    total_amount INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT "pending",
    user INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: orders_33c3ebc3
DROP TABLE IF EXISTS orders_33c3ebc3;

-- Drop table: products_1161b936
DROP TABLE IF EXISTS products_1161b936;

-- Drop table: users_d388e915
DROP TABLE IF EXISTS users_d388e915;
""",
        description="test_query_optimization_3a23cf31",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
