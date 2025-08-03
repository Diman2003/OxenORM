"""
Migration: 20250803_21555983201_test_query_optimization_1f9c508f

test_query_optimization_1f9c508f

Generated on: 2025-08-03T16:25:59.832044
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="ad873871-a719-4b43-b225-4d2e5510f9fe",
        name="20250803_21555983201_test_query_optimization_1f9c508f",
        version="20250803215559832",
        up_sql="""-- Create table: users_911ea933
CREATE TABLE users_911ea933 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: products_c391dcc9
CREATE TABLE products_c391dcc9 (
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

-- Create table: orders_fe8bc40a
CREATE TABLE orders_fe8bc40a (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    total_amount INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT "pending",
    user INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: orders_fe8bc40a
DROP TABLE IF EXISTS orders_fe8bc40a;

-- Drop table: products_c391dcc9
DROP TABLE IF EXISTS products_c391dcc9;

-- Drop table: users_911ea933
DROP TABLE IF EXISTS users_911ea933;
""",
        description="test_query_optimization_1f9c508f",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="ad873871-a719-4b43-b225-4d2e5510f9fe",
        name="20250803_21555983201_test_query_optimization_1f9c508f",
        version="20250803215559832",
        up_sql="""-- Create table: users_911ea933
CREATE TABLE users_911ea933 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: products_c391dcc9
CREATE TABLE products_c391dcc9 (
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

-- Create table: orders_fe8bc40a
CREATE TABLE orders_fe8bc40a (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    total_amount INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT "pending",
    user INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: orders_fe8bc40a
DROP TABLE IF EXISTS orders_fe8bc40a;

-- Drop table: products_c391dcc9
DROP TABLE IF EXISTS products_c391dcc9;

-- Drop table: users_911ea933
DROP TABLE IF EXISTS users_911ea933;
""",
        description="test_query_optimization_1f9c508f",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
