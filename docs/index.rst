============
OxenORM
============

OxenORM is a high-performance Python Object-Relational Mapper backed by Rust, delivering **10-20× speed-ups** versus popular pure-Python ORMs while maintaining full Python compatibility.

.. note::
   OxenORM is a production-ready project with comprehensive features and excellent performance.
   We maintain a `Changelog <https://github.com/Diman2003/OxenORM/blob/main/CHANGELOG.md>`_ for all updates.

Source & issue trackers are available at `<https://github.com/Diman2003/OxenORM/>`_

OxenORM supports CPython 3.9+ for SQLite, MySQL, and PostgreSQL with async-first design.

Introduction
============

Why was OxenORM built?
-----------------------

OxenORM was built to provide a high-performance, async-native Object-Relational Mapper for Python that combines the familiar Django-like API with the blazing-fast performance of Rust.

OxenORM performs exceptionally well when compared to other Python ORMs. In our benchmarks, we measure different read and write operations (rows/sec, more is better), and OxenORM consistently outperforms all competitors:

.. image:: _static/performance_comparison.png
    :target: https://github.com/Diman2003/OxenORM

How is an ORM useful?
---------------------

An Object-Relational Mapper (ORM) abstracts database interactions, allowing developers to work with databases using high-level, object-oriented code instead of raw SQL.

* Reduces boilerplate SQL, allowing faster development with cleaner, more readable code.
* Helps prevent SQL injection by using parameterized queries.
* Centralized schema and relationship definitions make code easier to manage and modify.
* Handles schema changes through version-controlled migrations.
* Provides type safety and IDE autocomplete support.

Features
========

High-Performance Rust Backend
------------------------------
OxenORM's core database operations are implemented in Rust, providing:

* **10-20× faster** performance than traditional Python ORMs
* **Memory safety** guaranteed by Rust's type system
* **Zero-copy data transfer** via PyO3 FFI
* **Async I/O** with Tokio runtime
* **Connection pooling** with health checks

Clean, familiar Python interface
--------------------------------
Model definitions:

.. code-block:: python3

    from oxen import Model
    from oxen.fields import CharField, IntField

    class Tournament(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=255)


Operations on models, queries and complex aggregations:

.. code-block:: python3

    # Creating a record
    await Tournament.create(name='Another Tournament')

    # Searching for a record
    tour = await Tournament.filter(name__contains='Another').first()
    print(tour.name)

    # Count groups of records with a complex condition
    await Tournament.annotate(
        name_prefix=Case(
            When(name__startswith="One", then="1"),
            When(name__startswith="Two", then="2"),
            default="0",
        ),
    ).annotate(
        count=Count(F("name_prefix")),
    ).group_by(
        "name_prefix"
    ).values("name_prefix", "count")


See :ref:`getting_started` for a more detailed guide.

Pluggable Database backends
---------------------------
OxenORM currently supports the following :ref:`databases`:

* `PostgreSQL` >= 9.4 (using ``asyncpg``)
* `SQLite` (using ``aiosqlite``)
* `MySQL`/`MariaDB` (using ``aiomysql``)

Multi-database support
---------------------
Connect to multiple databases simultaneously:

.. code-block:: python3

    from oxen import MultiDatabaseManager

    manager = MultiDatabaseManager({
        'primary': 'postgresql://user:pass@localhost/primary',
        'analytics': 'mysql://user:pass@localhost/analytics',
        'cache': 'sqlite://:memory:'
    })

Advanced Features
----------------
OxenORM supports the following advanced features:

* Composable, Django-inspired :ref:`models`
* Supports relations, such as ``ForeignKeyField`` and ``ManyToManyField``
* Supports many standard :ref:`fields` including advanced types
* Comprehensive :ref:`query_api` with complex expressions
* :ref:`transactions` with rollback support
* :ref:`migration` system for schema management
* :ref:`cli` tools for database management
* :ref:`logging` with structured output
* :ref:`performance` monitoring and optimization

Production Ready
---------------
OxenORM includes production-ready features:

* **CLI Tools**: Database management, migrations, benchmarking
* **Configuration Management**: Environment-based settings
* **Advanced Logging**: Structured JSON output
* **Security Features**: File upload validation
* **Performance Monitoring**: Detailed metrics and profiling
* **Error Handling**: Comprehensive validation systems

Installation
===========

Basic Installation
-----------------

.. code-block:: bash

    pip install oxen-orm

Database-Specific Installation
-----------------------------

.. list-table:: Available Installation Options
   :header-rows: 1
   :widths: 30 70

   * - Database
     - Installation Command
   * - SQLite
     - ``pip install oxen-orm``
   * - PostgreSQL
     - ``pip install "oxen-orm[postgres]"``
   * - MySQL
     - ``pip install "oxen-orm[mysql]"``

Development Installation
-----------------------

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/Diman2003/OxenORM.git
    cd OxenORM

    # Install in development mode
    pip install -e .

    # Build Rust extension
    maturin develop

Quick Start
==========

Define your models:

.. code-block:: python3

    from oxen import Model
    from oxen.fields import CharField, IntField

    class User(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=100)
        email = CharField(max_length=255, unique=True)

Connect to database and create tables:

.. code-block:: python3

    from oxen import connect

    async def main():
        # Connect to database
        await connect("sqlite://:memory:")
        
        # Create tables
        await User.create_table()
        
        # Create records
        user = await User.create(name="John Doe", email="john@example.com")
        
        # Query records
        users = await User.filter(name__contains="John")
        for user in users:
            print(f"Found user: {user.name}")

    # Run the async function
    import asyncio
    asyncio.run(main())

See :ref:`getting_started` for a more detailed guide.

Performance
==========

OxenORM delivers exceptional performance through its Rust backend:

* **10-20× faster** than SQLAlchemy, Tortoise ORM, and Django ORM
* **Zero-copy data transfer** via PyO3 FFI
* **Memory safety** guaranteed by Rust
* **Async I/O** with Tokio runtime
* **Query caching** with TTL support
* **Connection pooling** with health checks

See :ref:`performance` for detailed benchmarks and optimization guides.

Architecture
===========

OxenORM uses a hybrid architecture combining Python and Rust:

* **Python Layer**: Models, QuerySet API, CLI tools, configuration
* **PyO3 Bridge**: Type conversion, async wrapper, error handling
* **Rust Core**: SQL builder, executor, connection pool, migrations
* **Database Layer**: PostgreSQL, MySQL, SQLite support

This architecture provides the best of both worlds: familiar Python APIs with Rust-level performance.

Contributing
===========

We welcome contributions! Please see our :ref:`contributing` guide for details.

* Check out issues first, and then create a PR
* Follow our code style guidelines
* Add tests for new functionality
* Update documentation for new features

Support
=======

* **Documentation**: This site
* **Issues**: `GitHub Issues <https://github.com/Diman2003/OxenORM/issues>`_
* **Discussions**: `GitHub Discussions <https://github.com/Diman2003/OxenORM/discussions>`_
* **Discord**: Join our community

License
=======

This project is licensed under the MIT License - see the `LICENSE <https://github.com/Diman2003/OxenORM/blob/main/LICENSE>`_ file for details.
