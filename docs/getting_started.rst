.. _getting_started:

===============
Getting started
===============

Installation
===============
The following table shows the available installation options for different databases:

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

Optional Dependencies
---------------------
The following libraries can be used to improve performance:

* `orjson <https://pypi.org/project/orjson/>`_: Automatically used if installed for JSON SerDes.
* `uvloop <https://pypi.org/project/uvloop/>`_: Shown to improve performance as an alternative to ``asyncio``.
* `ciso8601 <https://pypi.org/project/ciso8601/>`_: Automatically used if installed.
  Not automatically installed on Windows due to often a lack of a C compiler. Default on Linux/CPython.

The following command will install all optional dependencies:

.. code-block:: bash

    pip install "oxen-orm[dev]"

Tutorial
========

Define the models by inheriting from ``oxen.Model``.

.. code-block:: python3

    from oxen import Model
    from oxen.fields import CharField, IntField, BooleanField

    class Tournament(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=255)
        is_active = BooleanField(default=True)

    class Event(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=255)
        tournament = IntField()  # Foreign key reference
        participants = CharField(max_length=1000)  # JSON field for many-to-many

    class Team(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=255)

.. note::
   You can read more on defining models in :ref:`models`

After defining the models, OxenORM needs to be initialized to establish the relationships between models and connect to the database.
The code below creates a connection to a SQLite DB database. ``create_table`` sets up schema on an empty database.

.. code-block:: python3

    from oxen import connect
    import asyncio

    async def main():
        # Here we connect to a SQLite DB file.
        await connect('sqlite://db.sqlite3')
        
        # Create tables
        await Tournament.create_table()
        await Event.create_table()
        await Team.create_table()

    asyncio.run(main())

With OxenORM initialized, the models are available for use:

.. code-block:: python3

    async def main():
        await connect('sqlite://db.sqlite3')
        
        # Create tables
        await Tournament.create_table()
        await Event.create_table()
        await Team.create_table()

        # Creating an instance with .save()
        tournament = Tournament(name='New Tournament')
        await tournament.save()

        # Or with .create()
        await Event.create(name='Without participants', tournament=tournament.id)
        event = await Event.create(name='Test', tournament=tournament.id)
        
        # Create teams
        participants = []
        for i in range(2):
            team = await Team.create(name=f'Team {i + 1}')
            participants.append(team)

        # Update event with participants (JSON field)
        event.participants = [team.id for team in participants]
        await event.save()

        # Query records
        all_tournaments = await Tournament.all()
        for tour in all_tournaments:
            print(f"Tournament: {tour.name}")

        # Filter records
        active_tournaments = await Tournament.filter(is_active=True)
        for tour in active_tournaments:
            print(f"Active tournament: {tour.name}")

        # Complex queries
        events_with_teams = await Event.filter(
            name__contains="Test"
        ).order_by('-id').limit(5)
        
        for event in events_with_teams:
            print(f"Event: {event.name}")

    asyncio.run(main())

.. note::
    Find more examples (including transactions, using multiple databases and more complex querying) in :ref:`examples` and :ref:`query_api`.

Advanced Usage
=============

Multi-Database Support
---------------------

OxenORM supports connecting to multiple databases simultaneously:

.. code-block:: python3

    from oxen import MultiDatabaseManager

    async def multi_db_example():
        manager = MultiDatabaseManager({
            'primary': 'postgresql://user:pass@localhost/primary',
            'analytics': 'mysql://user:pass@localhost/analytics',
            'cache': 'sqlite://:memory:'
        })
        
        # Use different databases for different models
        await User.objects.using('primary').create(name="User")
        await AnalyticsEvent.objects.using('analytics').create(event="page_view")

Complex Queries
--------------

OxenORM supports advanced query features:

.. code-block:: python3

    # Complex filtering
    users = await User.filter(
        age__gte=18,
        email__contains="@gmail.com"
    ).exclude(
        is_active=False
    ).order_by('-created_at').limit(10)

    # Aggregations
    user_count = await User.count()
    active_users = await User.filter(is_active=True).count()

    # Bulk operations
    users_to_create = [
        User(name=f"User {i}", email=f"user{i}@example.com")
        for i in range(100)
    ]
    created_users = await User.bulk_create(users_to_create)

Transactions
-----------

OxenORM supports database transactions:

.. code-block:: python3

    from oxen import connect

    async def transaction_example():
        await connect("sqlite://:memory:")
        
        async with connect.transaction() as tx:
            # All operations in this block are in a transaction
            user1 = await User.create(name="User 1", email="user1@example.com")
            user2 = await User.create(name="User 2", email="user2@example.com")
            
            # If any operation fails, the entire transaction is rolled back
            print(f"Created users: {user1.name}, {user2.name}")

CLI Tools
---------

OxenORM provides comprehensive CLI tools:

.. code-block:: bash

    # Database management
    oxen db init --url postgresql://user:pass@localhost/mydb
    oxen db status --url postgresql://user:pass@localhost/mydb

    # Migration management
    oxen migrate makemigrations --url postgresql://user:pass@localhost/mydb
    oxen migrate migrate --url postgresql://user:pass@localhost/mydb

    # Performance benchmarking
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --iterations 1000

    # Interactive shell
    oxen shell --url postgresql://user:pass@localhost/mydb --models myapp.models

    # Schema inspection
    oxen inspect --url postgresql://user:pass@localhost/mydb --output schema.json

Performance Features
===================

OxenORM includes several performance optimizations:

* **Connection Pooling**: Automatic connection management with health checks
* **Query Caching**: Intelligent caching with TTL support
* **Bulk Operations**: Efficient batch operations for large datasets
* **Async I/O**: Non-blocking database operations
* **Rust Backend**: High-performance core operations

See :ref:`performance` for detailed performance guides and benchmarks.

Production Configuration
======================

For production deployments, OxenORM supports comprehensive configuration:

.. code-block:: python3

    from oxen import connect
    from oxen.config import Config

    # Production configuration
    config = Config(
        databases={
            'default': 'postgresql://user:pass@localhost/prod_db',
            'read_replica': 'postgresql://user:pass@read-replica/prod_db',
        },
        logging={
            'level': 'INFO',
            'format': 'json',
        },
        performance={
            'connection_pool_size': 20,
            'query_cache_ttl': 300,
        }
    )
    
    await connect(config=config)

See :ref:`config` for detailed configuration options.
