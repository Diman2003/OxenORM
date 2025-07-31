"""
Migration: 20250731_11302195432_final_comprehensive_migration

Final comprehensive migration

Generated on: 2025-07-31T06:00:21.954351
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="09074439-80b4-47ab-a587-616fe1de8128",
        name="20250731_11302195432_final_comprehensive_migration",
        version="20250731113021954",
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
        id="09074439-80b4-47ab-a587-616fe1de8128",
        name="20250731_11302195432_final_comprehensive_migration",
        version="20250731113021954",
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
