Tutorials
========

This section provides comprehensive tutorials for OxenORM, covering all major features and use cases.

Getting Started
--------------

Quick Start Guide
~~~~~~~~~~~~~~~~

This tutorial will get you up and running with OxenORM in minutes.

1. **Installation**

   .. code-block:: bash

      pip install oxenorm

2. **Basic Setup**

   .. code-block:: python

      from oxen import Model, CharField, IntegerField, connect

      # Define your first model
      class User(Model):
          name = CharField(max_length=100)
          email = CharField(max_length=255, unique=True)
          age = IntegerField(default=0)

      # Connect to database
      await connect("sqlite:///test.db")

      # Create a user
      user = await User.create(name="John Doe", email="john@example.com", age=30)
      print(f"Created user: {user.name}")

3. **Query Users**

   .. code-block:: python

      # Get all users
      users = await User.all()
      print(f"Found {len(users)} users")

      # Get specific user
      user = await User.get(email="john@example.com")
      print(f"Found user: {user.name}")

      # Filter users
      young_users = await User.filter(age__lt=25)
      print(f"Found {len(young_users)} young users")

Model Definition
---------------

Basic Models
~~~~~~~~~~~

Models in OxenORM are defined using Python classes that inherit from ``Model``:

.. code-block:: python

    from oxen import Model, CharField, IntegerField, BooleanField, DateTimeField

    class Product(Model):
        name = CharField(max_length=200)
        price = IntegerField(default=0)
        description = CharField(max_length=500)
        is_active = BooleanField(default=True)
        created_at = DateTimeField(auto_now_add=True)

        class Meta:
            table_name = "products"

Field Types
~~~~~~~~~~

OxenORM supports a wide variety of field types:

**Basic Fields**

.. code-block:: python

    from oxen.fields import (
        CharField, TextField, IntegerField, FloatField, 
        BooleanField, DateTimeField, DateField, TimeField
    )

    class Example(Model):
        # Text fields
        name = CharField(max_length=100)
        description = TextField()
        
        # Numeric fields
        age = IntegerField(default=0)
        price = FloatField(default=0.0)
        
        # Boolean field
        is_active = BooleanField(default=True)
        
        # Date/time fields
        created_at = DateTimeField(auto_now_add=True)
        updated_at = DateTimeField(auto_now=True)
        birth_date = DateField()
        meeting_time = TimeField()

**Advanced Fields**

.. code-block:: python

    from oxen.fields import (
        UUIDField, JSONField, EmailField, URLField,
        FileField, ImageField, ArrayField
    )

    class AdvancedExample(Model):
        # UUID field
        id = UUIDField(primary_key=True)
        
        # JSON field
        metadata = JSONField(default=dict)
        
        # Email and URL fields
        email = EmailField(max_length=255)
        website = URLField(max_length=500)
        
        # File fields
        document = FileField(upload_to="documents/")
        photo = ImageField(upload_to="photos/")
        
        # Array field (PostgreSQL)
        tags = ArrayField(CharField(max_length=50))

**Relational Fields**

.. code-block:: python

    from oxen.fields.relational import ForeignKeyField, OneToOneField, ManyToManyField

    class Author(Model):
        name = CharField(max_length=100)
        email = CharField(max_length=255)

    class Book(Model):
        title = CharField(max_length=200)
        author = ForeignKeyField(Author, related_name="books")
        
    class BookDetail(Model):
        book = OneToOneField(Book, related_name="detail")
        pages = IntegerField(default=0)
        isbn = CharField(max_length=20)
        
    class Category(Model):
        name = CharField(max_length=100)
        books = ManyToManyField(Book, through="BookCategory")

CRUD Operations
--------------

Create Operations
~~~~~~~~~~~~~~~~

**Single Object Creation**

.. code-block:: python

    # Create a single object
    user = await User.create(
        name="Alice Johnson",
        email="alice@example.com",
        age=25
    )
    print(f"Created user with ID: {user.pk}")

**Bulk Creation**

.. code-block:: python

    # Create multiple objects at once
    users_data = [
        {"name": "Bob Smith", "email": "bob@example.com", "age": 30},
        {"name": "Carol Davis", "email": "carol@example.com", "age": 28},
        {"name": "David Wilson", "email": "david@example.com", "age": 35}
    ]
    
    users = await User.bulk_create(users_data)
    print(f"Created {len(users)} users")

Read Operations
~~~~~~~~~~~~~~

**Get All Objects**

.. code-block:: python

    # Get all users
    all_users = await User.all()
    print(f"Total users: {len(all_users)}")

**Get Single Object**

.. code-block:: python

    # Get by primary key
    user = await User.get(pk=1)
    
    # Get by field
    user = await User.get(email="alice@example.com")
    
    # Get or return None
    user = await User.get_or_none(email="nonexistent@example.com")

**Filter Objects**

.. code-block:: python

    # Simple filter
    active_users = await User.filter(is_active=True)
    
    # Complex filter
    young_active_users = await User.filter(
        age__lt=30,
        is_active=True,
        email__icontains="gmail"
    )
    
    # Multiple conditions
    users = await User.filter(
        Q(age__gte=18) & Q(is_active=True) | Q(email__endswith="@company.com")
    )

**Ordering and Limiting**

.. code-block:: python

    # Order by field
    users_by_age = await User.all().order_by("age")
    
    # Reverse order
    users_by_age_desc = await User.all().order_by("-age")
    
    # Multiple ordering
    users_ordered = await User.all().order_by("age", "-created_at")
    
    # Limit results
    recent_users = await User.all().order_by("-created_at").limit(10)
    
    # Offset and limit
    paginated_users = await User.all().offset(20).limit(10)

Update Operations
~~~~~~~~~~~~~~~~

**Update Single Object**

.. code-block:: python

    # Get and update
    user = await User.get(pk=1)
    await user.update(name="Updated Name", age=31)
    
    # Update directly
    await User.filter(pk=1).update(name="Updated Name", age=31)

**Bulk Updates**

.. code-block:: python

    # Update all active users
    await User.filter(is_active=True).update(last_login=datetime.now())
    
    # Update with conditions
    await User.filter(age__lt=18).update(is_minor=True)

Delete Operations
~~~~~~~~~~~~~~~~

**Delete Single Object**

.. code-block:: python

    # Get and delete
    user = await User.get(pk=1)
    await user.delete()
    
    # Delete directly
    await User.filter(pk=1).delete()

**Bulk Deletes**

.. code-block:: python

    # Delete all inactive users
    await User.filter(is_active=False).delete()
    
    # Delete with conditions
    await User.filter(created_at__lt=datetime(2020, 1, 1)).delete()

Advanced Queries
---------------

Complex Filtering
~~~~~~~~~~~~~~~~

**Field Lookups**

.. code-block:: python

    # Exact match
    users = await User.filter(name="John")
    
    # Case-insensitive contains
    users = await User.filter(name__icontains="john")
    
    # Starts with
    users = await User.filter(email__startswith="admin")
    
    # Ends with
    users = await User.filter(email__endswith="@company.com")
    
    # Greater than
    users = await User.filter(age__gt=18)
    
    # Less than or equal
    users = await User.filter(age__lte=65)
    
    # In list
    users = await User.filter(age__in=[25, 30, 35])
    
    # Not in list
    users = await User.filter(age__not_in=[18, 19, 20])

**Q Objects for Complex Queries**

.. code-block:: python

    from oxen import Q

    # AND condition
    users = await User.filter(
        Q(age__gte=18) & Q(is_active=True)
    )
    
    # OR condition
    users = await User.filter(
        Q(age__lt=18) | Q(age__gt=65)
    )
    
    # NOT condition
    users = await User.filter(
        ~Q(is_active=False)
    )
    
    # Complex combination
    users = await User.filter(
        Q(age__gte=18) & (Q(is_active=True) | Q(email__endswith="@admin.com"))
    )

Aggregations
~~~~~~~~~~~

**Basic Aggregations**

.. code-block:: python

    from oxen import Count, Sum, Avg, Max, Min

    # Count
    total_users = await User.all().count()
    
    # Sum
    total_age = await User.all().aggregate(Sum("age"))
    
    # Average
    avg_age = await User.all().aggregate(Avg("age"))
    
    # Maximum
    max_age = await User.all().aggregate(Max("age"))
    
    # Minimum
    min_age = await User.all().aggregate(Min("age"))

**Group By**

.. code-block:: python

    # Group by field
    age_groups = await User.all().group_by("age").aggregate(Count("id"))
    
    # Multiple aggregations
    stats = await User.all().group_by("is_active").aggregate(
        Count("id"),
        Avg("age"),
        Max("age")
    )

Window Functions
~~~~~~~~~~~~~~~

**Row Number**

.. code-block:: python

    from oxen import RowNumber

    # Add row numbers
    users_with_rank = await User.all().window(
        RowNumber().over().order_by("age")
    )

**Rank and Dense Rank**

.. code-block:: python

    from oxen import Rank, DenseRank

    # Rank by age
    users_ranked = await User.all().window(
        Rank().over().order_by("age")
    )
    
    # Dense rank by age
    users_dense_ranked = await User.all().window(
        DenseRank().over().order_by("age")
    )

**Lag and Lead**

.. code-block:: python

    from oxen import Lag, Lead

    # Compare with previous row
    users_with_lag = await User.all().window(
        Lag("age", 1).over().order_by("created_at")
    )
    
    # Compare with next row
    users_with_lead = await User.all().window(
        Lead("age", 1).over().order_by("created_at")
    )

Common Table Expressions (CTEs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Simple CTE**

.. code-block:: python

    from oxen import CommonTableExpression

    # Define CTE
    active_users_cte = CommonTableExpression(
        "active_users",
        User.filter(is_active=True)
    )
    
    # Use CTE in query
    result = await active_users_cte.select().filter(age__gte=18)

**Recursive CTE**

.. code-block:: python

    # Employee hierarchy example
    employee_hierarchy = CommonTableExpression(
        "employee_hierarchy",
        Employee.filter(manager_id__isnull=True)
        .union_all(
            Employee.join("employee_hierarchy", 
                         Employee.manager_id == "employee_hierarchy.id")
        )
    )

Relationships
------------

Foreign Key Relationships
~~~~~~~~~~~~~~~~~~~~~~~

**One-to-Many**

.. code-block:: python

    class Author(Model):
        name = CharField(max_length=100)
        email = CharField(max_length=255)

    class Book(Model):
        title = CharField(max_length=200)
        author = ForeignKeyField(Author, related_name="books")
        published_year = IntegerField()

    # Create related objects
    author = await Author.create(name="Jane Austen", email="jane@example.com")
    book = await Book.create(
        title="Pride and Prejudice",
        author=author,
        published_year=1813
    )

    # Access related objects
    author_books = await author.books.all()
    book_author = await book.author

**One-to-One**

.. code-block:: python

    class User(Model):
        name = CharField(max_length=100)
        email = CharField(max_length=255)

    class UserProfile(Model):
        user = OneToOneField(User, related_name="profile")
        bio = CharField(max_length=500)
        avatar = CharField(max_length=255)

    # Create related objects
    user = await User.create(name="John Doe", email="john@example.com")
    profile = await UserProfile.create(
        user=user,
        bio="Software developer",
        avatar="avatar.jpg"
    )

    # Access related objects
    user_profile = await user.profile
    profile_user = await profile.user

**Many-to-Many**

.. code-block:: python

    class Book(Model):
        title = CharField(max_length=200)
        author = ForeignKeyField(Author, related_name="books")

    class Category(Model):
        name = CharField(max_length=100)
        books = ManyToManyField(Book, through="BookCategory")

    class BookCategory(Model):
        book = ForeignKeyField(Book, related_name="category_links")
        category = ForeignKeyField(Category, related_name="book_links")

    # Create related objects
    book = await Book.create(title="Python Programming", author=author)
    category = await Category.create(name="Programming")
    
    # Add relationship
    await book.categories.add(category)
    
    # Query related objects
    book_categories = await book.categories.all()
    category_books = await category.books.all()

Lazy Loading
~~~~~~~~~~~

**Automatic Lazy Loading**

.. code-block:: python

    # Lazy loading is enabled by default
    book = await Book.get(pk=1)
    
    # Access related object (loaded on demand)
    author = await book.author
    print(f"Book: {book.title}, Author: {author.name}")

**Eager Loading**

.. code-block:: python

    # Load related objects in advance
    books_with_authors = await Book.all().prefetch_related("author")
    
    for book in books_with_authors:
        # No additional query needed
        print(f"Book: {book.title}, Author: {book.author.name}")

Reverse Accessors
~~~~~~~~~~~~~~~~

**Automatic Reverse Accessors**

.. code-block:: python

    # Get all books by an author
    author = await Author.get(pk=1)
    author_books = await author.books.all()
    
    # Get user's profile
    user = await User.get(pk=1)
    profile = await user.profile
    
    # Get all books in a category
    category = await Category.get(pk=1)
    category_books = await category.books.all()

Transactions
-----------

**Basic Transactions**

.. code-block:: python

    from oxen import transaction

    async with transaction() as txn:
        # Create user
        user = await User.create(name="Alice", email="alice@example.com")
        
        # Create profile
        profile = await UserProfile.create(user=user, bio="Developer")
        
        # If any operation fails, all changes are rolled back
        await txn.commit()

**Nested Transactions**

.. code-block:: python

    async with transaction() as outer_txn:
        user = await User.create(name="Bob", email="bob@example.com")
        
        async with transaction() as inner_txn:
            profile = await UserProfile.create(user=user, bio="Designer")
            await inner_txn.commit()
        
        await outer_txn.commit()

**Manual Transaction Control**

.. code-block:: python

    txn = await transaction()
    
    try:
        user = await User.create(name="Charlie", email="charlie@example.com")
        profile = await UserProfile.create(user=user, bio="Manager")
        await txn.commit()
    except Exception:
        await txn.rollback()
        raise

Migrations
---------

**Creating Migrations**

.. code-block:: bash

    # Generate migration
    oxen migrate makemigrations --url sqlite:///test.db

**Applying Migrations**

.. code-block:: bash

    # Apply migrations
    oxen migrate migrate --url sqlite:///test.db

**Migration Status**

.. code-block:: bash

    # Check migration status
    oxen migrate status --url sqlite:///test.db

**Rollback Migrations**

.. code-block:: bash

    # Rollback last migration
    oxen migrate rollback --url sqlite:///test.db

Performance Optimization
----------------------

**Query Optimization**

.. code-block:: python

    from oxen import QueryOptimizer

    # Analyze query performance
    optimizer = QueryOptimizer()
    
    # Get query plan
    queryset = User.filter(age__gte=18)
    plan = await optimizer.analyze_query(queryset)
    
    # Get optimization suggestions
    suggestions = await optimizer.get_suggestions(queryset)

**Caching**

.. code-block:: python

    # Enable query caching
    from oxen import set_cache_enabled
    set_cache_enabled(True)
    
    # Cached queries
    users = await User.all()  # Results cached
    users = await User.all()  # Results from cache

**Bulk Operations**

.. code-block:: python

    # Bulk create for better performance
    users_data = [{"name": f"User {i}", "email": f"user{i}@example.com"} 
                  for i in range(1000)]
    users = await User.bulk_create(users_data)
    
    # Bulk update
    await User.filter(is_active=True).bulk_update({"last_login": datetime.now()})

Monitoring and Debugging
-----------------------

**Performance Monitoring**

.. code-block:: python

    from oxen import MonitoringDashboard

    # Get performance metrics
    dashboard = MonitoringDashboard()
    metrics = await dashboard.get_metrics()
    
    # Get query statistics
    query_stats = await dashboard.get_query_stats()

**Query Logging**

.. code-block:: python

    import logging
    from oxen import set_log_level

    # Enable query logging
    set_log_level(logging.DEBUG)
    
    # All queries will be logged
    users = await User.all()

**Admin Interface**

.. code-block:: python

    from oxen.admin import start_admin_interface

    # Start admin interface
    start_admin_interface(host="localhost", port=8080)
    
    # Open http://localhost:8080 in your browser

Best Practices
-------------

**Model Design**

.. code-block:: python

    class User(Model):
        # Use meaningful field names
        name = CharField(max_length=100)
        email = CharField(max_length=255, unique=True)
        
        # Add indexes for frequently queried fields
        age = IntegerField(db_index=True)
        
        # Use appropriate field types
        created_at = DateTimeField(auto_now_add=True)
        updated_at = DateTimeField(auto_now=True)
        
        class Meta:
            table_name = "users"
            # Add table-level constraints
            constraints = [
                "CHECK (age >= 0)",
                "CHECK (email LIKE '%@%')"
            ]

**Query Optimization**

.. code-block:: python

    # Use select_related for foreign keys
    books_with_authors = await Book.all().select_related("author")
    
    # Use prefetch_related for reverse foreign keys
    authors_with_books = await Author.all().prefetch_related("books")
    
    # Use only() to select specific fields
    user_names = await User.all().only("name")
    
    # Use defer() to exclude specific fields
    users_without_email = await User.all().defer("email")

**Error Handling**

.. code-block:: python

    from oxen import DoesNotExist, MultipleObjectsReturned

    try:
        user = await User.get(email="user@example.com")
    except DoesNotExist:
        print("User not found")
    except MultipleObjectsReturned:
        print("Multiple users found")

**Connection Management**

.. code-block:: python

    from oxen import connect, disconnect

    # Connect at application startup
    await connect("postgresql://user:pass@localhost/mydb")
    
    # Disconnect at application shutdown
    await disconnect()

**Async Best Practices**

.. code-block:: python

    # Use async/await consistently
    async def get_user_stats():
        total_users = await User.all().count()
        active_users = await User.filter(is_active=True).count()
        return {"total": total_users, "active": active_users}
    
    # Handle concurrent operations
    async def create_multiple_users(users_data):
        tasks = [User.create(**data) for data in users_data]
        return await asyncio.gather(*tasks)

Troubleshooting
--------------

**Common Issues**

1. **Database Connection Errors**

   .. code-block:: python

       # Check connection string
       await connect("sqlite:///test.db")
       
       # Check database permissions
       # Ensure database file is writable

2. **Migration Issues**

   .. code-block:: bash

       # Reset migrations
       oxen migrate reset --url sqlite:///test.db
       
       # Check migration status
       oxen migrate status --url sqlite:///test.db

3. **Performance Issues**

   .. code-block:: python

       # Enable query logging
       import logging
       logging.getLogger("oxen").setLevel(logging.DEBUG)
       
       # Use query optimization
       from oxen import QueryOptimizer
       optimizer = QueryOptimizer()
       suggestions = await optimizer.get_suggestions(queryset)

4. **Memory Issues**

   .. code-block:: python

       # Use pagination for large datasets
       users = await User.all().offset(0).limit(100)
       
       # Use streaming for very large datasets
       async for user in User.all().stream():
           process_user(user)

**Debugging Tips**

1. **Enable Debug Mode**

   .. code-block:: python

       import logging
       logging.basicConfig(level=logging.DEBUG)

2. **Use Admin Interface**

   .. code-block:: python

       from oxen.admin import start_admin_interface
       start_admin_interface()

3. **Monitor Performance**

   .. code-block:: python

       from oxen import MonitoringDashboard
       dashboard = MonitoringDashboard()
       metrics = await dashboard.get_metrics() 