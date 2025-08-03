API Reference
============

This section provides a comprehensive reference for all OxenORM APIs.

Core Classes
-----------

Model
~~~~~

The base class for all OxenORM models.

**Class Definition**

.. code-block:: python

    class Model:
        """Base class for all OxenORM models."""
        
        class Meta:
            table_name: str = None
            db_table: str = None
            abstract: bool = False
            constraints: List[str] = []
            indexes: List[str] = []

**Meta Options**

- ``table_name``: Custom table name for the model
- ``db_table``: Alias for table_name (deprecated)
- ``abstract``: If True, model won't create a table
- ``constraints``: List of table-level constraints
- ``indexes``: List of table-level indexes

**Methods**

.. code-block:: python

    # Create operations
    @classmethod
    async def create(cls, **kwargs) -> Model
    
    @classmethod
    async def bulk_create(cls, objects_data: List[Dict]) -> List[Model]
    
    # Read operations
    @classmethod
    async def all(cls, using_db=None) -> List[Model]
    
    @classmethod
    async def get(cls, **kwargs) -> Model
    
    @classmethod
    async def get_or_none(cls, **kwargs) -> Optional[Model]
    
    @classmethod
    async def filter(cls, *args, **kwargs) -> QuerySet
    
    # Update operations
    async def update(self, **kwargs) -> None
    
    async def save(self, force_insert=False, force_update=False) -> None
    
    # Delete operations
    async def delete(self) -> None
    
    @classmethod
    async def bulk_update(cls, objects: List[Model], fields: List[str]) -> None

QuerySet
~~~~~~~~

Represents a database query that can be chained and executed.

**Class Definition**

.. code-block:: python

    class QuerySet:
        """Represents a database query."""
        
        def __init__(self, model_class, db=None)

**Methods**

.. code-block:: python

    # Filtering
    def filter(self, *args, **kwargs) -> QuerySet
    
    def exclude(self, *args, **kwargs) -> QuerySet
    
    # Ordering
    def order_by(self, *fields) -> QuerySet
    
    def reverse(self) -> QuerySet
    
    # Limiting
    def limit(self, limit: int) -> QuerySet
    
    def offset(self, offset: int) -> QuerySet
    
    # Aggregations
    def count(self) -> int
    
    def aggregate(self, *aggregations) -> Dict
    
    def group_by(self, *fields) -> QuerySet
    
    # Window functions
    def window(self, *window_functions) -> QuerySet
    
    # CTEs
    def with_cte(self, *ctes) -> QuerySet
    
    # Related objects
    def select_related(self, *fields) -> QuerySet
    
    def prefetch_related(self, *fields) -> QuerySet
    
    def only(self, *fields) -> QuerySet
    
    def defer(self, *fields) -> QuerySet
    
    # Execution
    async def _execute(self) -> List[Model]
    
    async def first(self) -> Optional[Model]
    
    async def last(self) -> Optional[Model]
    
    # Update and delete
    async def update(self, **kwargs) -> int
    
    async def delete(self) -> int
    
    # Streaming
    def stream(self) -> AsyncIterator[Model]

Q Objects
~~~~~~~~~

Represents a database query condition.

**Class Definition**

.. code-block:: python

    class Q:
        """Represents a database query condition."""
        
        def __init__(self, **kwargs)
        
        def __and__(self, other) -> Q
        
        def __or__(self, other) -> Q
        
        def __invert__(self) -> Q

**Usage Examples**

.. code-block:: python

    from oxen import Q
    
    # Simple condition
    Q(name="John")
    
    # Complex condition
    Q(age__gte=18) & Q(is_active=True)
    
    # OR condition
    Q(age__lt=18) | Q(age__gt=65)
    
    # NOT condition
    ~Q(is_active=False)

Field Types
----------

Basic Fields
~~~~~~~~~~~

CharField
^^^^^^^^^

A field for storing character data.

.. code-block:: python

    class CharField(Field):
        def __init__(self, max_length: int = None, **kwargs)

**Parameters**

- ``max_length``: Maximum length of the string
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

TextField
^^^^^^^^^

A field for storing large text data.

.. code-block:: python

    class TextField(Field):
        def __init__(self, **kwargs)

**Parameters**

- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

IntegerField
^^^^^^^^^^^

A field for storing integer values.

.. code-block:: python

    class IntegerField(Field):
        def __init__(self, **kwargs)

**Parameters**

- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``auto_increment``: If True, auto-increment field
- ``help_text``: Help text for the field

FloatField
^^^^^^^^^^

A field for storing floating-point values.

.. code-block:: python

    class FloatField(Field):
        def __init__(self, **kwargs)

**Parameters**

- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

BooleanField
^^^^^^^^^^^

A field for storing boolean values.

.. code-block:: python

    class BooleanField(Field):
        def __init__(self, **kwargs)

**Parameters**

- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

DateTimeField
^^^^^^^^^^^^

A field for storing date and time values.

.. code-block:: python

    class DateTimeField(Field):
        def __init__(self, auto_now=False, auto_now_add=False, **kwargs)

**Parameters**

- ``auto_now``: If True, update field on every save
- ``auto_now_add``: If True, set field on creation only
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

DateField
^^^^^^^^^

A field for storing date values.

.. code-block:: python

    class DateField(Field):
        def __init__(self, **kwargs)

**Parameters**

- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

TimeField
^^^^^^^^^

A field for storing time values.

.. code-block:: python

    class TimeField(Field):
        def __init__(self, **kwargs)

**Parameters**

- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

Advanced Fields
~~~~~~~~~~~~~~

UUIDField
^^^^^^^^^

A field for storing UUID values.

.. code-block:: python

    class UUIDField(Field):
        def __init__(self, primary_key=False, **kwargs)

**Parameters**

- ``primary_key``: If True, use as primary key
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

JSONField
^^^^^^^^^

A field for storing JSON data.

.. code-block:: python

    class JSONField(Field):
        def __init__(self, **kwargs)

**Parameters**

- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

EmailField
^^^^^^^^^^

A field for storing email addresses.

.. code-block:: python

    class EmailField(Field):
        def __init__(self, max_length=254, **kwargs)

**Parameters**

- ``max_length``: Maximum length of the email
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

URLField
^^^^^^^^

A field for storing URLs.

.. code-block:: python

    class URLField(Field):
        def __init__(self, max_length=200, **kwargs)

**Parameters**

- ``max_length``: Maximum length of the URL
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

FileField
^^^^^^^^^

A field for storing file paths.

.. code-block:: python

    class FileField(Field):
        def __init__(self, upload_to="", **kwargs)

**Parameters**

- ``upload_to``: Directory to upload files to
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

ImageField
^^^^^^^^^^

A field for storing image file paths.

.. code-block:: python

    class ImageField(FileField):
        def __init__(self, upload_to="", **kwargs)

**Parameters**

- ``upload_to``: Directory to upload images to
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

ArrayField
^^^^^^^^^^

A field for storing arrays (PostgreSQL only).

.. code-block:: python

    class ArrayField(Field):
        def __init__(self, base_field, **kwargs)

**Parameters**

- ``base_field``: Field type for array elements
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

Relational Fields
~~~~~~~~~~~~~~~~

ForeignKeyField
^^^^^^^^^^^^^^^

A field for creating foreign key relationships.

.. code-block:: python

    class ForeignKeyField(RelationalField):
        def __init__(self, to, related_name=None, on_delete=None, **kwargs)

**Parameters**

- ``to``: Target model class
- ``related_name``: Name for reverse relationship
- ``on_delete``: Action on delete (CASCADE, SET_NULL, etc.)
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

OneToOneField
^^^^^^^^^^^^^

A field for creating one-to-one relationships.

.. code-block:: python

    class OneToOneField(RelationalField):
        def __init__(self, to, related_name=None, on_delete=None, **kwargs)

**Parameters**

- ``to``: Target model class
- ``related_name``: Name for reverse relationship
- ``on_delete``: Action on delete (CASCADE, SET_NULL, etc.)
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

ManyToManyField
^^^^^^^^^^^^^^^

A field for creating many-to-many relationships.

.. code-block:: python

    class ManyToManyField(RelationalField):
        def __init__(self, to, through=None, related_name=None, **kwargs)

**Parameters**

- ``to``: Target model class
- ``through``: Intermediate model for custom relationships
- ``related_name``: Name for reverse relationship
- ``unique``: If True, field must be unique
- ``null``: If True, field can be NULL
- ``default``: Default value for the field
- ``db_index``: If True, create database index
- ``help_text``: Help text for the field

Aggregations
-----------

Count
~~~~~

Count the number of objects.

.. code-block:: python

    class Count(Aggregation):
        def __init__(self, field="*", distinct=False)

**Parameters**

- ``field``: Field to count (default: "*")
- ``distinct``: If True, count distinct values

Sum
~~~

Sum the values of a field.

.. code-block:: python

    class Sum(Aggregation):
        def __init__(self, field)

**Parameters**

- ``field``: Field to sum

Avg
~~~

Calculate the average of a field.

.. code-block:: python

    class Avg(Aggregation):
        def __init__(self, field)

**Parameters**

- ``field``: Field to average

Max
~~~

Find the maximum value of a field.

.. code-block:: python

    class Max(Aggregation):
        def __init__(self, field)

**Parameters**

- ``field``: Field to find maximum of

Min
~~~

Find the minimum value of a field.

.. code-block:: python

    class Min(Aggregation):
        def __init__(self, field)

**Parameters**

- ``field``: Field to find minimum of

Window Functions
---------------

RowNumber
~~~~~~~~~

Add row numbers to results.

.. code-block:: python

    class RowNumber(WindowFunction):
        def __init__(self):
            super().__init__("ROW_NUMBER")

Rank
~~~~

Add rank to results.

.. code-block:: python

    class Rank(WindowFunction):
        def __init__(self):
            super().__init__("RANK")

DenseRank
~~~~~~~~~

Add dense rank to results.

.. code-block:: python

    class DenseRank(WindowFunction):
        def __init__(self):
            super().__init__("DENSE_RANK")

Lag
~~~

Get value from previous row.

.. code-block:: python

    class Lag(WindowFunction):
        def __init__(self, field, offset=1):
            super().__init__("LAG", field, offset)

**Parameters**

- ``field``: Field to lag
- ``offset``: Number of rows to lag

Lead
~~~~~

Get value from next row.

.. code-block:: python

    class Lead(WindowFunction):
        def __init__(self, field, offset=1):
            super().__init__("LEAD", field, offset)

**Parameters**

- ``field``: Field to lead
- ``offset``: Number of rows to lead

Common Table Expressions
------------------------

CommonTableExpression
~~~~~~~~~~~~~~~~~~~~~

Create a common table expression.

.. code-block:: python

    class CommonTableExpression:
        def __init__(self, name, query, recursive=False)

**Parameters**

- ``name``: Name of the CTE
- ``query``: QuerySet for the CTE
- ``recursive``: If True, create recursive CTE

Database Connection
------------------

connect
~~~~~~~

Connect to a database.

.. code-block:: python

    async def connect(url: str, **kwargs) -> None

**Parameters**

- ``url``: Database connection URL
- ``**kwargs``: Additional connection parameters

**Supported URLs**

- SQLite: ``sqlite:///path/to/database.db``
- PostgreSQL: ``postgresql://user:pass@host:port/database``
- MySQL: ``mysql://user:pass@host:port/database``

disconnect
~~~~~~~~~~

Disconnect from the database.

.. code-block:: python

    async def disconnect() -> None

set_database_for_models
~~~~~~~~~~~~~~~~~~~~~~~

Set the database connection for all models.

.. code-block:: python

    def set_database_for_models(database) -> None

**Parameters**

- ``database``: Database connection object

Transactions
------------

transaction
~~~~~~~~~~~

Create a database transaction.

.. code-block:: python

    async def transaction() -> Transaction

**Usage**

.. code-block:: python

    async with transaction() as txn:
        # Database operations
        await txn.commit()

Transaction
~~~~~~~~~~

Represents a database transaction.

**Methods**

.. code-block:: python

    async def commit(self) -> None
    async def rollback(self) -> None

Signals
-------

pre_save
~~~~~~~~

Signal sent before saving a model.

.. code-block:: python

    pre_save = Signal()

post_save
~~~~~~~~~

Signal sent after saving a model.

.. code-block:: python

    post_save = Signal()

pre_delete
~~~~~~~~~~

Signal sent before deleting a model.

.. code-block:: python

    pre_delete = Signal()

post_delete
~~~~~~~~~~~

Signal sent after deleting a model.

.. code-block:: python

    post_delete = Signal()

**Usage**

.. code-block:: python

    from oxen import pre_save, post_save

    @pre_save.connect
    async def handle_pre_save(sender, instance, **kwargs):
        print(f"About to save {instance}")

    @post_save.connect
    async def handle_post_save(sender, instance, created, **kwargs):
        print(f"Saved {instance}, created: {created}")

Migrations
----------

MigrationEngine
~~~~~~~~~~~~~~

Engine for managing database migrations.

.. code-block:: python

    class MigrationEngine:
        def __init__(self, database_url: str)

**Methods**

.. code-block:: python

    async def create_migrations_table(self) -> None
    async def get_applied_migrations(self) -> List[str]
    async def apply_migration(self, migration_file: str) -> None
    async def rollback_migration(self, migration_file: str) -> None

MigrationGenerator
~~~~~~~~~~~~~~~~~

Generator for creating migration files.

.. code-block:: python

    class MigrationGenerator:
        def __init__(self, models: List[Type[Model]])

**Methods**

.. code-block:: python

    def generate_migration(self, name: str) -> str
    def get_sql_statements(self) -> List[str]

MigrationRunner
~~~~~~~~~~~~~~

Runner for executing migrations.

.. code-block:: python

    class MigrationRunner:
        def __init__(self, database_url: str)

**Methods**

.. code-block:: python

    async def run_migrations(self, migration_dir: str) -> None
    async def rollback_migrations(self, migration_dir: str, steps: int = 1) -> None
    async def get_migration_status(self, migration_dir: str) -> Dict

Performance Monitoring
---------------------

QueryOptimizer
~~~~~~~~~~~~~

Optimizer for analyzing and improving query performance.

.. code-block:: python

    class QueryOptimizer:
        def __init__(self)

**Methods**

.. code-block:: python

    async def analyze_query(self, queryset: QuerySet) -> QueryPlan
    async def get_suggestions(self, queryset: QuerySet) -> List[str]
    async def optimize_query(self, queryset: QuerySet) -> QuerySet

MonitoringDashboard
~~~~~~~~~~~~~~~~~~

Dashboard for monitoring database performance.

.. code-block:: python

    class MonitoringDashboard:
        def __init__(self)

**Methods**

.. code-block:: python

    async def get_metrics(self) -> Dict[str, Any]
    async def get_alerts(self) -> List[Alert]
    async def add_alert(self, alert: Alert) -> None
    async def export_data(self) -> Dict[str, Any]

Admin Interface
--------------

AdminInterface
~~~~~~~~~~~~~

Interface for managing database schemas and models.

.. code-block:: python

    class AdminInterface:
        def __init__(self)

**Methods**

.. code-block:: python

    def register_models(self, models: List[Type[Model]]) -> None
    def get_schema_summary(self) -> Dict[str, Any]
    def get_table_details(self, table_name: str) -> Optional[Dict[str, Any]]
    def generate_schema_diagram(self) -> Dict[str, Any]
    def export_schema_json(self, filename: str) -> None

Benchmarking
------------

BenchmarkRunner
~~~~~~~~~~~~~~

Runner for performance benchmarking.

.. code-block:: python

    class BenchmarkRunner:
        def __init__(self)

**Methods**

.. code-block:: python

    def create_suite(self, name: str, description: str = "") -> BenchmarkSuite
    async def run_benchmark(self, test_name: str, operation: Callable, 
                           iterations: int = 1000, warmup_iterations: int = 100) -> BenchmarkResult
    def generate_report(self, suite_name: str) -> Dict[str, Any]
    def save_report(self, suite_name: str, filename: Optional[str] = None) -> Path

Exceptions
----------

OxenError
~~~~~~~~~

Base exception for all OxenORM errors.

.. code-block:: python

    class OxenError(Exception):
        pass

ConfigurationError
~~~~~~~~~~~~~~~~~

Raised when there's a configuration error.

.. code-block:: python

    class ConfigurationError(OxenError):
        pass

ConnectionError
~~~~~~~~~~~~~~

Raised when there's a database connection error.

.. code-block:: python

    class ConnectionError(OxenError):
        pass

ValidationError
~~~~~~~~~~~~~~

Raised when field validation fails.

.. code-block:: python

    class ValidationError(OxenError):
        pass

IntegrityError
~~~~~~~~~~~~~

Raised when database integrity constraints are violated.

.. code-block:: python

    class IntegrityError(OxenError):
        pass

DoesNotExist
~~~~~~~~~~~

Raised when a requested object doesn't exist.

.. code-block:: python

    class DoesNotExist(OxenError):
        pass

MultipleObjectsReturned
~~~~~~~~~~~~~~~~~~~~~~

Raised when multiple objects are returned when only one was expected.

.. code-block:: python

    class MultipleObjectsReturned(OxenError):
        pass

OperationalError
~~~~~~~~~~~~~~~

Raised when there's a database operation error.

.. code-block:: python

    class OperationalError(OxenError):
        pass

TransactionError
~~~~~~~~~~~~~~~

Raised when there's a transaction error.

.. code-block:: python

    class TransactionError(OxenError):
        pass

CLI Commands
-----------

Database Management
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Initialize database
    oxen db init --url <database_url>
    
    # Check database status
    oxen db status --url <database_url>
    
    # Create tables
    oxen db create-tables --url <database_url>

Migration Management
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Generate migrations
    oxen migrate makemigrations --url <database_url>
    
    # Apply migrations
    oxen migrate migrate --url <database_url>
    
    # Check migration status
    oxen migrate status --url <database_url>
    
    # Rollback migrations
    oxen migrate rollback --url <database_url> --steps <number>

Performance Testing
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run performance benchmarks
    oxen benchmark performance --url <database_url> --iterations <number>
    
    # Generate performance report
    oxen benchmark report --output <filename>

Admin Interface
~~~~~~~~~~~~~~

.. code-block:: bash

    # Start admin interface
    oxen admin start --host <host> --port <port>
    
    # Open admin interface in browser
    oxen admin open --url <admin_url> 