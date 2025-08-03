"""
Migration: 20250803_21060609338_test_advanced_queries_1fb3a8e0

test_advanced_queries_1fb3a8e0

Generated on: 2025-08-03T15:36:06.093425
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="ca66a866-0025-41bc-8391-59fed72e6224",
        name="20250803_21060609338_test_advanced_queries_1fb3a8e0",
        version="20250803210606093",
        up_sql="""-- Create table: sales_orders_63663ed0
CREATE TABLE sales_orders_63663ed0 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    region VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: employees_11b9cd9d
CREATE TABLE employees_11b9cd9d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary INTEGER NOT NULL DEFAULT 0,
    hire_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: employees_11b9cd9d
DROP TABLE IF EXISTS employees_11b9cd9d;

-- Drop table: sales_orders_63663ed0
DROP TABLE IF EXISTS sales_orders_63663ed0;
""",
        description="test_advanced_queries_1fb3a8e0",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="ca66a866-0025-41bc-8391-59fed72e6224",
        name="20250803_21060609338_test_advanced_queries_1fb3a8e0",
        version="20250803210606093",
        up_sql="""-- Create table: sales_orders_63663ed0
CREATE TABLE sales_orders_63663ed0 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    region VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: employees_11b9cd9d
CREATE TABLE employees_11b9cd9d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary INTEGER NOT NULL DEFAULT 0,
    hire_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: employees_11b9cd9d
DROP TABLE IF EXISTS employees_11b9cd9d;

-- Drop table: sales_orders_63663ed0
DROP TABLE IF EXISTS sales_orders_63663ed0;
""",
        description="test_advanced_queries_1fb3a8e0",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
