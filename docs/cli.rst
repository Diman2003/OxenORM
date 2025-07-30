.. _cli:

======
CLI
======

OxenORM provides a comprehensive command-line interface for database management, migrations, and development tasks.

Installation
===========

The CLI is automatically installed with OxenORM:

.. code-block:: bash

    pip install oxen-orm

Basic Usage
==========

The CLI is accessed via the ``oxen`` command:

.. code-block:: bash

    oxen --help
    oxen <command> --help

Database Management
==================

Initialize Database
-----------------

Initialize a new database connection and create tables:

.. code-block:: bash

    # Initialize with connection string
    oxen db init --url postgresql://user:pass@localhost/mydb
    
    # Initialize with config file
    oxen db init --config config.yaml
    
    # Initialize with environment variables
    oxen db init --env-file .env

Database Status
--------------

Check the status of your database connection:

.. code-block:: bash

    # Check connection status
    oxen db status --url postgresql://user:pass@localhost/mydb
    
    # Check with detailed information
    oxen db status --url postgresql://user:pass@localhost/mydb --verbose
    
    # Check multiple databases
    oxen db status --config multi_db_config.yaml

Schema Management
================

Create Tables
------------

Create tables for your models:

.. code-block:: bash

    # Create all tables
    oxen schema create --url postgresql://user:pass@localhost/mydb
    
    # Create specific tables
    oxen schema create --url postgresql://user:pass@localhost/mydb --models User,Post
    
    # Create with custom schema
    oxen schema create --url postgresql://user:pass@localhost/mydb --schema public

Drop Tables
-----------

Drop tables from the database:

.. code-block:: bash

    # Drop all tables
    oxen schema drop --url postgresql://user:pass@localhost/mydb
    
    # Drop specific tables
    oxen schema drop --url postgresql://user:pass@localhost/mydb --models User,Post
    
    # Drop with confirmation
    oxen schema drop --url postgresql://user:pass@localhost/mydb --confirm

Schema Inspection
----------------

Inspect the current database schema:

.. code-block:: bash

    # Show all tables
    oxen schema inspect --url postgresql://user:pass@localhost/mydb
    
    # Show specific table
    oxen schema inspect --url postgresql://user:pass@localhost/mydb --table users
    
    # Export schema to file
    oxen schema inspect --url postgresql://user:pass@localhost/mydb --output schema.json
    
    # Show with details
    oxen schema inspect --url postgresql://user:pass@localhost/mydb --verbose

Migration Management
===================

Create Migrations
----------------

Generate migration files for schema changes:

.. code-block:: bash

    # Create migration for all changes
    oxen migrate makemigrations --url postgresql://user:pass@localhost/mydb
    
    # Create migration for specific models
    oxen migrate makemigrations --url postgresql://user:pass@localhost/mydb --models User,Post
    
    # Create migration with custom name
    oxen migrate makemigrations --url postgresql://user:pass@localhost/mydb --name add_user_fields
    
    # Create migration with custom path
    oxen migrate makemigrations --url postgresql://user:pass@localhost/mydb --migrations-dir ./migrations

Apply Migrations
---------------

Apply pending migrations to the database:

.. code-block:: bash

    # Apply all pending migrations
    oxen migrate migrate --url postgresql://user:pass@localhost/mydb
    
    # Apply specific migration
    oxen migrate migrate --url postgresql://user:pass@localhost/mydb --migration 0001_initial
    
    # Apply with fake flag (for testing)
    oxen migrate migrate --url postgresql://user:pass@localhost/mydb --fake
    
    # Apply with dry-run
    oxen migrate migrate --url postgresql://user:pass@localhost/mydb --dry-run

Migration Status
---------------

Check the status of migrations:

.. code-block:: bash

    # Show migration status
    oxen migrate show --url postgresql://user:pass@localhost/mydb
    
    # Show with details
    oxen migrate show --url postgresql://user:pass@localhost/mydb --verbose
    
    # Show specific migration
    oxen migrate show --url postgresql://user:pass@localhost/mydb --migration 0001_initial

Rollback Migrations
-------------------

Rollback applied migrations:

.. code-block:: bash

    # Rollback last migration
    oxen migrate rollback --url postgresql://user:pass@localhost/mydb
    
    # Rollback specific number of migrations
    oxen migrate rollback --url postgresql://user:pass@localhost/mydb --steps 3
    
    # Rollback to specific migration
    oxen migrate rollback --url postgresql://user:pass@localhost/mydb --to 0001_initial

Performance Tools
================

Performance Benchmarking
-----------------------

Run performance benchmarks on your database:

.. code-block:: bash

    # Run basic performance test
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb
    
    # Run with custom iterations
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --iterations 1000
    
    # Run specific benchmarks
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --benchmarks crud,query,bulk
    
    # Run with custom data size
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --data-size 10000
    
    # Export results to file
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --output results.json

Performance Monitoring
---------------------

Monitor database performance in real-time:

.. code-block:: bash

    # Start performance monitoring
    oxen monitor start --url postgresql://user:pass@localhost/mydb
    
    # Monitor with custom interval
    oxen monitor start --url postgresql://user:pass@localhost/mydb --interval 5
    
    # Monitor specific metrics
    oxen monitor start --url postgresql://user:pass@localhost/mydb --metrics queries,connections,performance
    
    # Export monitoring data
    oxen monitor start --url postgresql://user:pass@localhost/mydb --output monitoring.log

Development Tools
================

Interactive Shell
----------------

Start an interactive Python shell with OxenORM:

.. code-block:: bash

    # Start interactive shell
    oxen shell --url postgresql://user:pass@localhost/mydb
    
    # Start with specific models
    oxen shell --url postgresql://user:pass@localhost/mydb --models User,Post
    
    # Start with custom Python path
    oxen shell --url postgresql://user:pass@localhost/mydb --python-path ./myapp
    
    # Start with custom environment
    oxen shell --url postgresql://user:pass@localhost/mydb --env-file .env

Code Generation
--------------

Generate code templates and boilerplate:

.. code-block:: bash

    # Generate model template
    oxen generate model User --fields name:CharField,email:CharField,age:IntField
    
    # Generate migration template
    oxen generate migration add_user_fields --models User
    
    # Generate API template
    oxen generate api User --methods create,read,update,delete
    
    # Generate test template
    oxen generate test User --coverage

Data Management
==============

Data Import
-----------

Import data from various sources:

.. code-block:: bash

    # Import from CSV
    oxen data import --url postgresql://user:pass@localhost/mydb --file users.csv --model User
    
    # Import from JSON
    oxen data import --url postgresql://user:pass@localhost/mydb --file users.json --model User
    
    # Import with custom mapping
    oxen data import --url postgresql://user:pass@localhost/mydb --file users.csv --model User --mapping name:full_name,email:email_address
    
    # Import with validation
    oxen data import --url postgresql://user:pass@localhost/mydb --file users.csv --model User --validate

Data Export
-----------

Export data to various formats:

.. code-block:: bash

    # Export to CSV
    oxen data export --url postgresql://user:pass@localhost/mydb --model User --output users.csv
    
    # Export to JSON
    oxen data export --url postgresql://user:pass@localhost/mydb --model User --output users.json
    
    # Export with filters
    oxen data export --url postgresql://user:pass@localhost/mydb --model User --filter "is_active=True" --output active_users.csv
    
    # Export with custom fields
    oxen data export --url postgresql://user:pass@localhost/mydb --model User --fields name,email --output user_names.csv

Configuration
============

Configuration Files
------------------

OxenORM CLI supports configuration files:

.. code-block:: yaml

    # config.yaml
    databases:
      default:
        url: postgresql://user:pass@localhost/mydb
        pool_size: 10
        max_overflow: 20
      analytics:
        url: mysql://user:pass@localhost/analytics
        pool_size: 5
    
    logging:
      level: INFO
      format: json
      file: oxenorm.log
    
    performance:
      query_cache_ttl: 300
      connection_pool_health_check: true

Using configuration files:

.. code-block:: bash

    # Use config file
    oxen db init --config config.yaml
    
    # Use specific database from config
    oxen db status --config config.yaml --database analytics

Environment Variables
--------------------

OxenORM CLI supports environment variables:

.. code-block:: bash

    # Set database URL
    export OXENORM_DATABASE_URL="postgresql://user:pass@localhost/mydb"
    
    # Set log level
    export OXENORM_LOG_LEVEL="DEBUG"
    
    # Use environment variables
    oxen db init
    oxen db status

Command Options
==============

Global Options
-------------

All commands support these global options:

.. code-block:: bash

    --help, -h          Show help message
    --version, -v       Show version information
    --verbose, -V       Enable verbose output
    --quiet, -q         Suppress output
    --config, -c        Configuration file path
    --env-file, -e      Environment file path

Database Options
---------------

Database-related commands support:

.. code-block:: bash

    --url, -u           Database connection URL
    --database, -d      Database name (for multi-database configs)
    --timeout, -t       Connection timeout in seconds
    --pool-size, -p     Connection pool size
    --ssl-mode          SSL mode (disable, allow, prefer, require)

Output Options
-------------

Commands that produce output support:

.. code-block:: bash

    --output, -o        Output file path
    --format, -f        Output format (json, csv, table, yaml)
    --pretty, -P        Pretty-print output
    --no-color          Disable colored output

Examples
========

Complete Workflow
----------------

Here's a complete workflow example:

.. code-block:: bash

    # 1. Initialize database
    oxen db init --url postgresql://user:pass@localhost/mydb
    
    # 2. Create initial migration
    oxen migrate makemigrations --url postgresql://user:pass@localhost/mydb --name initial
    
    # 3. Apply migration
    oxen migrate migrate --url postgresql://user:pass@localhost/mydb
    
    # 4. Import initial data
    oxen data import --url postgresql://user:pass@localhost/mydb --file users.csv --model User
    
    # 5. Run performance test
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --iterations 1000
    
    # 6. Start monitoring
    oxen monitor start --url postgresql://user:pass@localhost/mydb --interval 10

Development Workflow
-------------------

Development workflow with OxenORM CLI:

.. code-block:: bash

    # 1. Start development shell
    oxen shell --url postgresql://user:pass@localhost/mydb --models User,Post
    
    # 2. Make model changes in Python shell
    # ... make changes ...
    
    # 3. Generate migration for changes
    oxen migrate makemigrations --url postgresql://user:pass@localhost/mydb --name add_user_fields
    
    # 4. Apply migration
    oxen migrate migrate --url postgresql://user:pass@localhost/mydb
    
    # 5. Test performance
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --benchmarks crud
    
    # 6. Export test data
    oxen data export --url postgresql://user:pass@localhost/mydb --model User --output test_users.csv

Production Deployment
--------------------

Production deployment workflow:

.. code-block:: bash

    # 1. Check database status
    oxen db status --url postgresql://user:pass@localhost/prod_db --verbose
    
    # 2. Apply migrations
    oxen migrate migrate --url postgresql://user:pass@localhost/prod_db
    
    # 3. Import production data
    oxen data import --url postgresql://user:pass@localhost/prod_db --file prod_data.csv --model User --validate
    
    # 4. Start monitoring
    oxen monitor start --url postgresql://user:pass@localhost/prod_db --interval 30 --output prod_monitoring.log
    
    # 5. Run performance benchmarks
    oxen benchmark performance --url postgresql://user:pass@localhost/prod_db --iterations 5000 --output prod_benchmarks.json

Troubleshooting
==============

Common Issues
------------

**Connection Issues:**

.. code-block:: bash

    # Test connection
    oxen db status --url postgresql://user:pass@localhost/mydb --verbose
    
    # Check SSL settings
    oxen db status --url postgresql://user:pass@localhost/mydb --ssl-mode require
    
    # Check timeout settings
    oxen db status --url postgresql://user:pass@localhost/mydb --timeout 30

**Migration Issues:**

.. code-block:: bash

    # Check migration status
    oxen migrate show --url postgresql://user:pass@localhost/mydb --verbose
    
    # Rollback problematic migration
    oxen migrate rollback --url postgresql://user:pass@localhost/mydb --steps 1
    
    # Fake migration (mark as applied without running)
    oxen migrate migrate --url postgresql://user:pass@localhost/mydb --fake

**Performance Issues:**

.. code-block:: bash

    # Run detailed performance test
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --iterations 10000 --verbose
    
    # Monitor in real-time
    oxen monitor start --url postgresql://user:pass@localhost/mydb --interval 5 --metrics all
    
    # Check connection pool
    oxen db status --url postgresql://user:pass@localhost/mydb --verbose

Debug Mode
----------

Enable debug mode for troubleshooting:

.. code-block:: bash

    # Enable debug logging
    export OXENORM_LOG_LEVEL="DEBUG"
    oxen db status --url postgresql://user:pass@localhost/mydb --verbose
    
    # Enable SQL logging
    export OXENORM_LOG_SQL="true"
    oxen migrate migrate --url postgresql://user:pass@localhost/mydb --verbose
    
    # Enable performance logging
    export OXENORM_LOG_PERFORMANCE="true"
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --verbose
