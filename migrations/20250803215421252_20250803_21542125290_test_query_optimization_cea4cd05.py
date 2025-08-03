"""
Migration: 20250803_21542125290_test_query_optimization_cea4cd05

test_query_optimization_cea4cd05

Generated on: 2025-08-03T16:24:21.252936
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="29a7a725-f471-49f6-96cc-c2fec68109b9",
        name="20250803_21542125290_test_query_optimization_cea4cd05",
        version="20250803215421252",
        up_sql="""-- Create table: users_79ee45ff
CREATE TABLE users_79ee45ff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: products_14be53ee
CREATE TABLE products_14be53ee (
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

-- Create table: orders_3f7ec0fb
CREATE TABLE orders_3f7ec0fb (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    total_amount INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT "pending",
    user INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: orders_3f7ec0fb
DROP TABLE IF EXISTS orders_3f7ec0fb;

-- Drop table: products_14be53ee
DROP TABLE IF EXISTS products_14be53ee;

-- Drop table: users_79ee45ff
DROP TABLE IF EXISTS users_79ee45ff;
""",
        description="test_query_optimization_cea4cd05",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="29a7a725-f471-49f6-96cc-c2fec68109b9",
        name="20250803_21542125290_test_query_optimization_cea4cd05",
        version="20250803215421252",
        up_sql="""-- Create table: users_79ee45ff
CREATE TABLE users_79ee45ff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: products_14be53ee
CREATE TABLE products_14be53ee (
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

-- Create table: orders_3f7ec0fb
CREATE TABLE orders_3f7ec0fb (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    total_amount INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT "pending",
    user INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: orders_3f7ec0fb
DROP TABLE IF EXISTS orders_3f7ec0fb;

-- Drop table: products_14be53ee
DROP TABLE IF EXISTS products_14be53ee;

-- Drop table: users_79ee45ff
DROP TABLE IF EXISTS users_79ee45ff;
""",
        description="test_query_optimization_cea4cd05",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
