OxenORM CLI Tool
================

The OxenORM CLI tool provides a command-line interface for managing database migrations and other OxenORM operations.

Installation
-----------

The CLI tool is included with OxenORM and can be installed via pip:

.. code-block:: bash

    pip install oxen-orm

Or install from source:

.. code-block:: bash

    git clone https://github.com/Diman2003/OxenORM.git
    cd OxenORM
    pip install -e .

Usage
-----

Basic usage:

.. code-block:: bash

    oxen [OPTIONS] COMMAND [ARGS]...

Global Options
-------------

- ``--database-url, -d``: Database connection URL (e.g., postgresql://user:pass@localhost/db)
- ``--migrations-dir, -m``: Directory for migration files (default: migrations)
- ``--verbose, -v``: Enable verbose output

You can also set the database URL using the ``OXEN_DATABASE_URL`` environment variable:

.. code-block:: bash

    export OXEN_DATABASE_URL="postgresql://user:pass@localhost/db"
    oxen migrate status

Migration Commands
-----------------

The CLI provides comprehensive migration management through the ``migrate`` subcommand.

Status
~~~~~~

Check the current migration status:

.. code-block:: bash

    oxen migrate status

Options:
- ``--format``: Output format (table, json, simple) - default: table

Examples:

.. code-block:: bash

    # Default table format
    oxen migrate status

    # JSON format for scripting
    oxen migrate status --format json

    # Simple format for quick overview
    oxen migrate status --format simple

Create
~~~~~~

Create a new migration:

.. code-block:: bash

    oxen migrate create "Description" [OPTIONS]

Options:
- ``--author``: Migration author
- ``--up-sql``: Up migration SQL (or use --file)
- ``--down-sql``: Down migration SQL (or use --file)
- ``--file``: SQL file containing up and down migrations

Examples:

.. code-block:: bash

    # Create migration with inline SQL
    oxen migrate create "Add users table" \
        --up-sql "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100));" \
        --down-sql "DROP TABLE users;" \
        --author "john.doe"

    # Create migration from SQL file
    oxen migrate create "Add posts table" --file migration.sql --author "jane.smith"

SQL File Format
^^^^^^^^^^^^^^

When using the ``--file`` option, the SQL file should contain up and down migrations separated by markers:

.. code-block:: sql

    -- UP
    CREATE TABLE posts (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        content TEXT,
        user_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- DOWN
    DROP TABLE posts;

Run
~~~

Run pending migrations:

.. code-block:: bash

    oxen migrate run [OPTIONS]

Options:
- ``--target``: Target migration version (default: run all pending)
- ``--dry-run``: Show what would be run without executing

Examples:

.. code-block:: bash

    # Run all pending migrations
    oxen migrate run

    # Run migrations up to a specific version
    oxen migrate run --target 20231201120000

    # Dry run to see what would be executed
    oxen migrate run --dry-run

Rollback
~~~~~~~~

Rollback migrations to a previous version:

.. code-block:: bash

    oxen migrate rollback TARGET_VERSION [OPTIONS]

Options:
- ``--dry-run``: Show what would be rolled back without executing

Examples:

.. code-block:: bash

    # Rollback to a specific version
    oxen migrate rollback 20231201120000

    # Dry run to see what would be rolled back
    oxen migrate rollback 20231201120000 --dry-run

History
~~~~~~~

Show migration history:

.. code-block:: bash

    oxen migrate history [OPTIONS]

Options:
- ``--limit``: Number of recent migrations to show (default: 10)
- ``--format``: Output format (table, json, simple) - default: table

Examples:

.. code-block:: bash

    # Show last 10 migrations
    oxen migrate history

    # Show last 5 migrations in JSON format
    oxen migrate history --limit 5 --format json

    # Show all migrations in simple format
    oxen migrate history --limit 0 --format simple

Validate
~~~~~~~~

Validate migration files:

.. code-block:: bash

    oxen migrate validate [OPTIONS]

Options:
- ``--migration``: Specific migration to validate (default: validate all)

Examples:

.. code-block:: bash

    # Validate all migrations
    oxen migrate validate

    # Validate a specific migration
    oxen migrate validate --migration 20231201120000

Output Formats
-------------

The CLI supports three output formats for status and history commands:

Table Format (Default)
~~~~~~~~~~~~~~~~~~~~~~

Human-readable table format:

.. code-block:: text

    Metric              | Value
    --------------------|------------------
    Applied Migrations  | 3
    Pending Migrations  | 2
    Current Version     | 20231201120000
    Latest Version      | 20231201130000

    📋 Applied Migrations (3):
      ✅ 20231201120000
      ✅ 20231201120001
      ✅ 20231201120002

    ⏳ Pending Migrations (2):
      ⏸️  20231201130000
      ⏸️  20231201130001

JSON Format
~~~~~~~~~~~

Machine-readable JSON format for scripting:

.. code-block:: json

    {
      "applied_count": 3,
      "pending_count": 2,
      "current_version": "20231201120000",
      "latest_version": "20231201130000",
      "applied_migrations": [
        "20231201120000",
        "20231201120001",
        "20231201120002"
      ],
      "pending_migrations": [
        "20231201130000",
        "20231201130001"
      ]
    }

Simple Format
~~~~~~~~~~~~

Simple key-value pairs:

.. code-block:: text

    applied_count: 3
    pending_count: 2
    current_version: 20231201120000
    latest_version: 20231201130000

Error Handling
-------------

The CLI provides clear error messages and validation:

- **Missing Database URL**: Prompts to use ``--database-url`` or set ``OXEN_DATABASE_URL``
- **Invalid Database URL**: Shows connection error details
- **Missing Subcommands**: Provides help for available commands
- **Migration Validation**: Checks SQL syntax and dependencies
- **Dry Run Mode**: Shows what would happen without making changes

Examples
--------

Complete Workflow
~~~~~~~~~~~~~~~~

Here's a complete example of using the CLI for a typical migration workflow:

.. code-block:: bash

    # 1. Check current status
    oxen migrate status

    # 2. Create a new migration
    oxen migrate create "Add user profiles" \
        --up-sql "CREATE TABLE profiles (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), bio TEXT);" \
        --down-sql "DROP TABLE profiles;" \
        --author "alice"

    # 3. Validate the migration
    oxen migrate validate

    # 4. Dry run to see what will happen
    oxen migrate run --dry-run

    # 5. Run the migration
    oxen migrate run

    # 6. Check status again
    oxen migrate status

    # 7. View history
    oxen migrate history --limit 5

Rollback Workflow
~~~~~~~~~~~~~~~~

Example of rolling back migrations:

.. code-block:: bash

    # 1. Check current status
    oxen migrate status

    # 2. See what would be rolled back
    oxen migrate rollback 20231201120000 --dry-run

    # 3. Perform the rollback
    oxen migrate rollback 20231201120000

    # 4. Verify the rollback
    oxen migrate status

Scripting
---------

The CLI is designed to be scriptable. Here are some examples:

Check Migration Status in Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    #!/bin/bash
    STATUS=$(oxen migrate status --format json)
    APPLIED_COUNT=$(echo "$STATUS" | jq -r '.applied_count')
    
    if [ "$APPLIED_COUNT" -gt 0 ]; then
        echo "Database has $APPLIED_COUNT applied migrations"
    else
        echo "Database has no applied migrations"
    fi

Automated Migration Runner
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    #!/bin/bash
    set -e
    
    echo "Running migrations..."
    
    # Check if there are pending migrations
    STATUS=$(oxen migrate status --format json)
    PENDING_COUNT=$(echo "$STATUS" | jq -r '.pending_count')
    
    if [ "$PENDING_COUNT" -gt 0 ]; then
        echo "Found $PENDING_COUNT pending migrations"
        
        # Run migrations
        oxen migrate run
        
        echo "Migrations completed successfully"
    else
        echo "No pending migrations"
    fi

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~~

**"Rust engine not available"**
    Build the Rust extension first: ``maturin develop``

**"Database URL is required"**
    Set the database URL: ``--database-url postgresql://user:pass@localhost/db``

**"Failed to connect to database"**
    Check your database connection string and ensure the database is running

**"Migration plan is invalid"**
    Check for dependency conflicts or invalid SQL in your migrations

**"Permission denied"**
    Ensure your database user has the necessary permissions

Debug Mode
~~~~~~~~~~

Use the ``--verbose`` flag for detailed error information:

.. code-block:: bash

    oxen --verbose migrate status

Environment Variables
~~~~~~~~~~~~~~~~~~~~

- ``OXEN_DATABASE_URL``: Default database connection URL
- ``OXEN_MIGRATIONS_DIR``: Default migrations directory

Integration
----------

The CLI integrates seamlessly with the OxenORM Python API. You can use the CLI for day-to-day operations and the Python API for programmatic access.

For more information about the Python API, see the :doc:`getting_started` guide.
