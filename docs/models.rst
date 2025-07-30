.. _models:

======
Models
======

.. rst-class:: emphasize-children

Usage
=====

All models should be derived from ``Model``. To start describing the models, import ``Model`` from ``oxen.models``.

.. code-block:: python3

    from oxen import Model

With that start describing the models

.. code-block:: python3

    from oxen import Model
    from oxen.fields import CharField, IntField, DateTimeField, DecimalField, BooleanField

    class Tournament(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=255)
        created = DateTimeField(auto_now_add=True)
        is_active = BooleanField(default=True)

        def __str__(self):
            return self.name

        class Meta:
            table_name = "tournaments"


    class Event(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=255)
        tournament_id = IntField()  # Foreign key reference
        participants = CharField(max_length=1000)  # JSON field for many-to-many
        modified = DateTimeField(auto_now=True)
        prize = DecimalField(max_digits=10, decimal_places=2, null=True)

        def __str__(self):
            return self.name

        class Meta:
            table_name = "events"


    class Team(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=255)

        def __str__(self):
            return self.name

        class Meta:
            table_name = "teams"

Let's look at the details of what we accomplished here:

.. code-block:: python3

    class Tournament(Model):

Every model should be derived from ``Model`` or its subclasses. Custom ``Model`` subclasses can be created in the following way:

.. code-block:: python3

    class AbstractTournament(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=255)
        created = DateTimeField(auto_now_add=True)

        class Meta:
            abstract = True

        def __str__(self):
            return self.name

This model will not affect the schema, but it will be available for inheritance.

Further we have field ``DateTimeField(auto_now=True)``. Options ``auto_now`` and ``auto_now_add`` work like Django's options.

Meta Options
-----------

OxenORM models support several Meta options:

.. code-block:: python3

    class User(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=100)
        email = CharField(max_length=255, unique=True)

        class Meta:
            table_name = "users"  # Custom table name
            abstract = False       # Whether this is an abstract model
            ordering = ["name"]    # Default ordering

Primary Keys
------------

In OxenORM, every model must have a primary key.

That primary key will be accessible through a reserved field ``pk`` which will be an alias of whichever field has been nominated as a primary key.
That alias field can be used as a field name when doing filtering e.g. ``.filter(pk=...)`` etc…

.. note::

    We currently support single (non-composite) primary keys of any indexable field type, but only these field types are recommended:

.. code-block:: python3

    IntField
    BigIntField
    CharField
    UUIDField

One must define a primary key by setting the ``primary_key`` parameter to ``True``.

Model Methods
============

CRUD Operations
--------------

OxenORM provides comprehensive CRUD operations:

.. code-block:: python3

    # Create
    user = await User.create(name="John Doe", email="john@example.com")
    
    # Read
    user = await User.get(id=1)
    users = await User.all()
    active_users = await User.filter(is_active=True)
    
    # Update
    user.name = "Jane Doe"
    await user.save()
    
    # Delete
    await user.delete()

Bulk Operations
--------------

OxenORM supports efficient bulk operations:

.. code-block:: python3

    # Bulk create
    users_to_create = [
        User(name=f"User {i}", email=f"user{i}@example.com")
        for i in range(100)
    ]
    created_users = await User.bulk_create(users_to_create)
    
    # Bulk update
    for user in users:
        user.is_active = False
    updated_count = await User.bulk_update(users, ['is_active'])
    
    # Bulk delete
    deleted_count = await User.filter(is_active=False).delete()

Query Methods
------------

OxenORM provides a rich query API:

.. code-block:: python3

    # Filtering
    users = await User.filter(age__gte=18, is_active=True)
    
    # Excluding
    users = await User.exclude(is_active=False)
    
    # Ordering
    users = await User.order_by('name', '-created_at')
    
    # Limiting and offsetting
    users = await User.limit(10).offset(20)
    
    # Counting
    user_count = await User.count()
    active_count = await User.filter(is_active=True).count()
    
    # Existence checks
    has_users = await User.exists()
    has_john = await User.filter(name__contains="John").exists()
    
    # First record
    first_user = await User.first()
    first_active = await User.filter(is_active=True).first()

Field Lookups
============

OxenORM supports Django-style field lookups:

.. code-block:: python3

    # Exact match
    users = await User.filter(name="John")
    
    # Case-insensitive contains
    users = await User.filter(name__icontains="john")
    
    # Starts with
    users = await User.filter(name__startswith="John")
    
    # Ends with
    users = await User.filter(name__endswith="Doe")
    
    # Greater than, less than
    users = await User.filter(age__gte=18, age__lte=65)
    
    # In list
    users = await User.filter(name__in=["John", "Jane", "Bob"])
    
    # Is null
    users = await User.filter(email__isnull=True)
    
    # Is not null
    users = await User.filter(email__isnull=False)

Complex Queries
==============

Q Objects
---------

OxenORM supports complex queries using Q objects:

.. code-block:: python3

    from oxen.queryset import Q

    # OR conditions
    users = await User.filter(
        Q(name__contains="John") | Q(email__contains="john")
    )
    
    # AND conditions
    users = await User.filter(
        Q(age__gte=18) & Q(is_active=True)
    )
    
    # NOT conditions
    users = await User.filter(
        ~Q(is_active=False)
    )

Aggregations
-----------

OxenORM supports database aggregations:

.. code-block:: python3

    from oxen.queryset import Count, Avg, Max, Min, Sum

    # Count
    user_count = await User.count()
    
    # Average age
    avg_age = await User.aggregate(avg_age=Avg('age'))
    
    # Maximum age
    max_age = await User.aggregate(max_age=Max('age'))
    
    # Sum of values
    total_value = await Order.aggregate(total=Sum('amount'))

Transactions
===========

OxenORM supports database transactions:

.. code-block:: python3

    from oxen import connect

    async def transfer_money(from_user_id, to_user_id, amount):
        async with connect.transaction() as tx:
            # Deduct from source account
            from_user = await User.get(id=from_user_id)
            from_user.balance -= amount
            await from_user.save()
            
            # Add to destination account
            to_user = await User.get(id=to_user_id)
            to_user.balance += amount
            await to_user.save()

Multi-Database Support
=====================

OxenORM supports using multiple databases:

.. code-block:: python3

    from oxen import MultiDatabaseManager

    # Initialize multi-database manager
    manager = MultiDatabaseManager({
        'primary': 'postgresql://user:pass@localhost/primary',
        'analytics': 'mysql://user:pass@localhost/analytics',
        'cache': 'sqlite://:memory:'
    })
    
    # Use specific database for operations
    user = await User.objects.using('primary').create(name="User")
    event = await AnalyticsEvent.objects.using('analytics').create(event="page_view")

Model Validation
===============

OxenORM supports model validation:

.. code-block:: python3

    from oxen.validators import MinValueValidator, MaxValueValidator

    class User(Model):
        id = IntField(primary_key=True)
        name = CharField(max_length=100)
        age = IntField(validators=[MinValueValidator(0), MaxValueValidator(120)])
        email = CharField(max_length=255, unique=True)

        def clean(self):
            # Custom validation
            if self.age < 18 and self.email.endswith('@adult.com'):
                raise ValidationError("Age restriction for adult content")

Performance Optimization
======================

OxenORM provides several performance optimization features:

.. code-block:: python3

    # Select only specific fields
    users = await User.filter(is_active=True).only('id', 'name')
    
    # Use bulk operations for large datasets
    users = await User.bulk_create(large_user_list)
    
    # Use transactions for multiple operations
    async with connect.transaction() as tx:
        # Multiple operations in single transaction
        pass

See :ref:`performance` for detailed performance optimization guides.
