"""
Migration: 20250731_11290995800_final_comprehensive_migration

Final comprehensive migration

Generated on: 2025-07-31T05:59:09.958065
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="e815a813-a682-4b1f-b0d3-f89e573f5656",
        name="20250731_11290995800_final_comprehensive_migration",
        version="20250731112909958",
        up_sql="""-- Create table: final_users
CREATE TABLE final_users (
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    age INTEGER NOT NULL,
    height REAL NOT NULL,
    salary DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    birth_date DATE NOT NULL,
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_data TEXT,
    metadata TEXT,
    jsonb_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: final_products
CREATE TABLE final_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: final_products
DROP TABLE IF EXISTS final_products;

-- Drop table: final_users
DROP TABLE IF EXISTS final_users;
""",
        description="Final comprehensive migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="e815a813-a682-4b1f-b0d3-f89e573f5656",
        name="20250731_11290995800_final_comprehensive_migration",
        version="20250731112909958",
        up_sql="""-- Create table: final_users
CREATE TABLE final_users (
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    age INTEGER NOT NULL,
    height REAL NOT NULL,
    salary DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    birth_date DATE NOT NULL,
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_data TEXT,
    metadata TEXT,
    jsonb_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: final_products
CREATE TABLE final_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: final_products
DROP TABLE IF EXISTS final_products;

-- Drop table: final_users
DROP TABLE IF EXISTS final_users;
""",
        description="Final comprehensive migration",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
