API Reference
============

This document provides a comprehensive reference for all OxenORM APIs, including models, fields, queries, and advanced features.

Models
------

Base Model
~~~~~~~~~

.. autoclass:: oxen.models.Model
   :members:
   :undoc-members:
   :show-inheritance:

Model Meta
~~~~~~~~~~

.. autoclass:: oxen.models.ModelMeta
   :members:
   :undoc-members:
   :show-inheritance:

Fields
------

Base Field
~~~~~~~~~~

.. autoclass:: oxen.fields.base.Field
   :members:
   :undoc-members:
   :show-inheritance:

Data Fields
~~~~~~~~~~~

Basic Types
^^^^^^^^^^^

.. autoclass:: oxen.fields.data.CharField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.TextField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.IntField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.IntegerField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.FloatField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.DecimalField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.BooleanField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.DateField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.DateTimeField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.TimeField
   :members:
   :undoc-members:

Advanced Types
^^^^^^^^^^^^^

.. autoclass:: oxen.fields.data.UUIDField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.JSONField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.JSONBField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.BinaryField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.FileField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.ImageField
   :members:
   :undoc-members:

PostgreSQL Specific
^^^^^^^^^^^^^^^^^^

.. autoclass:: oxen.fields.data.ArrayField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.RangeField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.HStoreField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.GeometryField
   :members:
   :undoc-members:

Specialized Types
^^^^^^^^^^^^^^^^

.. autoclass:: oxen.fields.data.EmailField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.URLField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.SlugField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.EnumField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.MoneyField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.data.InetField
   :members:
   :undoc-members:

Relational Fields
~~~~~~~~~~~~~~~~

.. autoclass:: oxen.fields.relational.ForeignKeyField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.relational.OneToOneField
   :members:
   :undoc-members:

.. autoclass:: oxen.fields.relational.ManyToManyField
   :members:
   :undoc-members:

QuerySet
--------

.. autoclass:: oxen.queryset.QuerySet
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: oxen.queryset.AwaitableQuery
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: oxen.queryset.QuerySetSingle
   :members:
   :undoc-members:
   :show-inheritance:

Manager
-------

.. autoclass:: oxen.manager.Manager
   :members:
   :undoc-members:
   :show-inheritance:

Expressions
-----------

Base Expressions
~~~~~~~~~~~~~~~

.. autoclass:: oxen.expressions.Q
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.F
   :members:
   :undoc-members:

Advanced Query Features
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: oxen.expressions.WindowFunction
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.CommonTableExpression
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.FullTextSearch
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.JSONPathQuery
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.ArrayOperation
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.CaseWhen
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.Subquery
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.AggregateFunction
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.DateFunction
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.StringFunction
   :members:
   :undoc-members:

.. autoclass:: oxen.expressions.MathFunction
   :members:
   :undoc-members:

Engine
------

.. autoclass:: oxen.engine.UnifiedEngine
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: oxen.engine.QueryCache
   :members:
   :undoc-members:

.. autoclass:: oxen.engine.PreparedStatementCache
   :members:
   :undoc-members:

.. autoclass:: oxen.engine.PerformanceMonitor
   :members:
   :undoc-members:

File Operations
--------------

.. autoclass:: oxen.file_operations.FileOperations
   :members:
   :undoc-members:

.. autoclass:: oxen.file_operations.FileManager
   :members:
   :undoc-members:

.. autoclass:: oxen.file_operations.ImageProcessor
   :members:
   :undoc-members:

Signals
-------

.. autoclass:: oxen.signals.Signals
   :members:
   :undoc-members:

Validators
----------

.. autoclass:: oxen.validators.Validator
   :members:
   :undoc-members:

Exceptions
----------

.. autoclass:: oxen.exceptions.ValidationError
   :members:
   :undoc-members:

.. autoclass:: oxen.exceptions.ModelError
   :members:
   :undoc-members:

.. autoclass:: oxen.exceptions.DoesNotExist
   :members:
   :undoc-members:

.. autoclass:: oxen.exceptions.MultipleObjectsReturned
   :members:
   :undoc-members:

.. autoclass:: oxen.exceptions.IncompleteInstanceError
   :members:
   :undoc-members:

.. autoclass:: oxen.exceptions.IntegrityError
   :members:
   :undoc-members:

.. autoclass:: oxen.exceptions.OperationalError
   :members:
   :undoc-members:

.. autoclass:: oxen.exceptions.ParamsError
   :members:
   :undoc-members:

Functions
---------

Connection Management
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: oxen.engine.connect

.. autofunction:: oxen.engine.disconnect

.. autofunction:: oxen.engine.get_global_performance_stats

.. autofunction:: oxen.engine.record_global_query

File Operations
~~~~~~~~~~~~~~

.. autofunction:: oxen.file_operations.read_file

.. autofunction:: oxen.file_operations.write_file

.. autofunction:: oxen.file_operations.resize_image

.. autofunction:: oxen.file_operations.create_thumbnail 