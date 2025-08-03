"""
Migration: 20250803_21034850794_test_fresh_update_operations_6b427c2d

test_fresh_update_operations_6b427c2d

Generated on: 2025-08-03T15:33:48.507981
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="b19365cb-77b6-44d6-9c05-db293e2d725c",
        name="20250803_21034850794_test_fresh_update_operations_6b427c2d",
        version="20250803210348507",
        up_sql="""-- Create table: update_test_users_9ab42e75
CREATE TABLE update_test_users_9ab42e75 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: update_test_products_aa92a405
CREATE TABLE update_test_products_aa92a405 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    description VARCHAR(500),
    is_available BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: update_test_products_aa92a405
DROP TABLE IF EXISTS update_test_products_aa92a405;

-- Drop table: update_test_users_9ab42e75
DROP TABLE IF EXISTS update_test_users_9ab42e75;
""",
        description="test_fresh_update_operations_6b427c2d",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="b19365cb-77b6-44d6-9c05-db293e2d725c",
        name="20250803_21034850794_test_fresh_update_operations_6b427c2d",
        version="20250803210348507",
        up_sql="""-- Create table: update_test_users_9ab42e75
CREATE TABLE update_test_users_9ab42e75 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: update_test_products_aa92a405
CREATE TABLE update_test_products_aa92a405 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    description VARCHAR(500),
    is_available BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: update_test_products_aa92a405
DROP TABLE IF EXISTS update_test_products_aa92a405;

-- Drop table: update_test_users_9ab42e75
DROP TABLE IF EXISTS update_test_users_9ab42e75;
""",
        description="test_fresh_update_operations_6b427c2d",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
