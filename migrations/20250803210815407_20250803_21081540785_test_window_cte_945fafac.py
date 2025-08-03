"""
Migration: 20250803_21081540785_test_window_cte_945fafac

test_window_cte_945fafac

Generated on: 2025-08-03T15:38:15.407889
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="6fc5ef27-0c77-467f-90d1-5569ead59281",
        name="20250803_21081540785_test_window_cte_945fafac",
        version="20250803210815407",
        up_sql="""-- Create table: sales_orders_09b84d5f
CREATE TABLE sales_orders_09b84d5f (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    region VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: employees_2c724728
CREATE TABLE employees_2c724728 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary INTEGER NOT NULL DEFAULT 0,
    hire_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: employees_2c724728
DROP TABLE IF EXISTS employees_2c724728;

-- Drop table: sales_orders_09b84d5f
DROP TABLE IF EXISTS sales_orders_09b84d5f;
""",
        description="test_window_cte_945fafac",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="6fc5ef27-0c77-467f-90d1-5569ead59281",
        name="20250803_21081540785_test_window_cte_945fafac",
        version="20250803210815407",
        up_sql="""-- Create table: sales_orders_09b84d5f
CREATE TABLE sales_orders_09b84d5f (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    region VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: employees_2c724728
CREATE TABLE employees_2c724728 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    salary INTEGER NOT NULL DEFAULT 0,
    hire_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: employees_2c724728
DROP TABLE IF EXISTS employees_2c724728;

-- Drop table: sales_orders_09b84d5f
DROP TABLE IF EXISTS sales_orders_09b84d5f;
""",
        description="test_window_cte_945fafac",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
