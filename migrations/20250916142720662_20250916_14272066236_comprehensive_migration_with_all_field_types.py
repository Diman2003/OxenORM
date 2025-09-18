"""
Migration: 20250916_14272066236_comprehensive_migration_with_all_field_types

Comprehensive migration with all field types

Generated on: 2025-09-16T08:57:20.662424
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="45cce9af-ff03-4561-bc7d-8c6fdf95aa11",
        name="20250916_14272066236_comprehensive_migration_with_all_field_types",
        version="20250916142720662",
        up_sql="""-- Create table: comprehensive_users
CREATE TABLE comprehensive_users (
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

-- Create table: comprehensive_products
CREATE TABLE comprehensive_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: comprehensive_products
DROP TABLE IF EXISTS comprehensive_products;

-- Drop table: comprehensive_users
DROP TABLE IF EXISTS comprehensive_users;
""",
        description="Comprehensive migration with all field types",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="45cce9af-ff03-4561-bc7d-8c6fdf95aa11",
        name="20250916_14272066236_comprehensive_migration_with_all_field_types",
        version="20250916142720662",
        up_sql="""-- Create table: comprehensive_users
CREATE TABLE comprehensive_users (
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

-- Create table: comprehensive_products
CREATE TABLE comprehensive_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: comprehensive_products
DROP TABLE IF EXISTS comprehensive_products;

-- Drop table: comprehensive_users
DROP TABLE IF EXISTS comprehensive_users;
""",
        description="Comprehensive migration with all field types",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
