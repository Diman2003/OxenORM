"""
Migration: 20250731_11220015969_basic_migration_with_simple_models

Basic migration with simple models

Generated on: 2025-07-31T05:52:00.159715
Author: test_runner
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="5a40e107-19ea-4311-ac9b-98e0747fb5c1",
        name="20250731_11220015969_basic_migration_with_simple_models",
        version="20250731112200159",
        up_sql="""-- Create table: simple_users
CREATE TABLE simple_users (
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    age INTEGER NOT NULL,
    height REAL NOT NULL,
    salary DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    birth_date DATE NOT NULL,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    profile_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_products
CREATE TABLE simple_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simpleproduct
DROP TABLE IF EXISTS simpleproduct;

-- Drop table: simpleuser
DROP TABLE IF EXISTS simpleuser;
""",
        description="Basic migration with simple models",
        author="test_runner",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="5a40e107-19ea-4311-ac9b-98e0747fb5c1",
        name="20250731_11220015969_basic_migration_with_simple_models",
        version="20250731112200159",
        up_sql="""-- Create table: simple_users
CREATE TABLE simple_users (
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    age INTEGER NOT NULL,
    height REAL NOT NULL,
    salary DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    birth_date DATE NOT NULL,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    profile_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table: simple_products
CREATE TABLE simple_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT True,
    created_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",
        down_sql="""-- Drop table: simpleproduct
DROP TABLE IF EXISTS simpleproduct;

-- Drop table: simpleuser
DROP TABLE IF EXISTS simpleuser;
""",
        description="Basic migration with simple models",
        author="test_runner",
        status=MigrationStatus.PENDING
    )
