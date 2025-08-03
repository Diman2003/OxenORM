"""
Migration: 20250803_21051013249_test_advanced_queries_02e374b0

test_advanced_queries_02e374b0

Generated on: 2025-08-03T15:35:10.132518
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="0a4401e0-6a8a-4922-891e-e27b5d09f0bb",
        name="20250803_21051013249_test_advanced_queries_02e374b0",
        version="20250803210510132",
        up_sql="""-- Create table: sales_orders_ea9b54ea
CREATE TABLE sales_orders_ea9b54ea (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0,
    order_date TIMESTAMP NOT NULL DEFAULT <function DateTimeField.__init__.<locals>.<lambda> at 0x100915bc0>,
    region VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: employees_fb444f90
CREATE TABLE employees_fb444f90 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary INTEGER NOT NULL DEFAULT 0,
    hire_date TIMESTAMP NOT NULL DEFAULT <function DateTimeField.__init__.<locals>.<lambda> at 0x1014b9bc0>,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: employees_fb444f90
DROP TABLE IF EXISTS employees_fb444f90;

-- Drop table: sales_orders_ea9b54ea
DROP TABLE IF EXISTS sales_orders_ea9b54ea;
""",
        description="test_advanced_queries_02e374b0",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="0a4401e0-6a8a-4922-891e-e27b5d09f0bb",
        name="20250803_21051013249_test_advanced_queries_02e374b0",
        version="20250803210510132",
        up_sql="""-- Create table: sales_orders_ea9b54ea
CREATE TABLE sales_orders_ea9b54ea (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0,
    order_date TIMESTAMP NOT NULL DEFAULT <function DateTimeField.__init__.<locals>.<lambda> at 0x100915bc0>,
    region VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: employees_fb444f90
CREATE TABLE employees_fb444f90 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary INTEGER NOT NULL DEFAULT 0,
    hire_date TIMESTAMP NOT NULL DEFAULT <function DateTimeField.__init__.<locals>.<lambda> at 0x1014b9bc0>,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: employees_fb444f90
DROP TABLE IF EXISTS employees_fb444f90;

-- Drop table: sales_orders_ea9b54ea
DROP TABLE IF EXISTS sales_orders_ea9b54ea;
""",
        description="test_advanced_queries_02e374b0",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
