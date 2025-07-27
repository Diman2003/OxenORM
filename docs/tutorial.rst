Tutorial
========

This tutorial series will guide you through OxenORM from basic usage to advanced features.

Getting Started
--------------

Installation
~~~~~~~~~~~

Install OxenORM using pip:

.. code-block:: bash

   pip install oxen-orm

For development installation:

.. code-block:: bash

   git clone https://github.com/your-org/oxen-orm.git
   cd oxen-orm
   pip install -e .

Basic Setup
~~~~~~~~~~

First, let's set up a basic database connection:

.. code-block:: python

   import asyncio
   from oxen import connect, disconnect

   async def main():
       # Connect to database
       await connect("sqlite://:memory:")
       
       # Your code here
       
       # Disconnect
       await disconnect()

   if __name__ == "__main__":
       asyncio.run(main())

Creating Models
~~~~~~~~~~~~~~

Define your first model:

.. code-block:: python

   from oxen import Model
   from oxen.fields import CharField, IntField, DateTimeField

   class User(Model):
       id = IntField(primary_key=True)
       username = CharField(max_length=50, unique=True)
       email = CharField(max_length=100, unique=True)
       created_at = DateTimeField(auto_now_add=True)

Basic CRUD Operations
--------------------

Creating Records
~~~~~~~~~~~~~~~

.. code-block:: python

   # Create a single user
   user = await User.create(
       username="john_doe",
       email="john@example.com"
   )
   print(f"Created user: {user.username}")

   # Create multiple users
   users = await User.bulk_create([
       User(username="jane_doe", email="jane@example.com"),
       User(username="bob_smith", email="bob@example.com")
   ])

Reading Records
~~~~~~~~~~~~~~

.. code-block:: python

   # Get a single user by ID
   user = await User.get(id=1)

   # Get a user by field
   user = await User.get(username="john_doe")

   # Get all users
   all_users = await User.all()

   # Filter users
   active_users = await User.filter(is_active=True)

   # Complex filtering
   recent_users = await User.filter(
       created_at__gte=datetime.now() - timedelta(days=7)
   )

Updating Records
~~~~~~~~~~~~~~~

.. code-block:: python

   # Update a single user
   user = await User.get(id=1)
   user.email = "new_email@example.com"
   await user.save()

   # Bulk update
   updated_count = await User.filter(is_active=False).update(is_active=True)

Deleting Records
~~~~~~~~~~~~~~~

.. code-block:: python

   # Delete a single user
   user = await User.get(id=1)
   await user.delete()

   # Bulk delete
   deleted_count = await User.filter(is_active=False).delete()

Advanced Queries
---------------

Complex Filtering
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen import Q

   # AND conditions
   users = await User.filter(
       Q(is_active=True) & Q(age__gte=18)
   )

   # OR conditions
   admins = await User.filter(
       Q(is_admin=True) | Q(is_moderator=True)
   )

   # NOT conditions
   non_admins = await User.filter(~Q(is_admin=True))

   # Complex combinations
   target_users = await User.filter(
       Q(is_active=True) & 
       (Q(age__gte=18) | Q(is_admin=True)) &
       ~Q(is_banned=True)
   )

Field Lookups
~~~~~~~~~~~~

.. code-block:: python

   # Exact match
   user = await User.get(username="john")

   # Case-insensitive contains
   users = await User.filter(username__icontains="john")

   # Starts with
   users = await User.filter(username__istartswith="j")

   # In list
   users = await User.filter(role__in=["admin", "moderator"])

   # Greater than
   adults = await User.filter(age__gte=18)

   # Is null
   users_without_bio = await User.filter(bio__isnull=True)

Ordering and Limiting
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Order by field
   users = await User.order_by("username")

   # Order by multiple fields
   users = await User.order_by("created_at", "-username")

   # Descending order
   recent_users = await User.order_by("-created_at")

   # Limit results
   top_users = await User.order_by("-score").limit(10)

   # Pagination
   page_1 = await User.limit(20).offset(0)
   page_2 = await User.limit(20).offset(20)

Aggregations
~~~~~~~~~~~

.. code-block:: python

   # Count
   user_count = await User.count()
   active_count = await User.filter(is_active=True).count()

   # Sum
   total_score = await User.aggregate(Sum("score"))

   # Average
   avg_age = await User.aggregate(Avg("age"))

   # Min/Max
   youngest = await User.aggregate(Min("age"))
   oldest = await User.aggregate(Max("age"))

   # Group by
   users_by_role = await User.values("role").annotate(
       count=Count("id"),
       avg_age=Avg("age")
   )

Relationships
------------

Foreign Keys
~~~~~~~~~~~

.. code-block:: python

   from oxen.fields import ForeignKeyField

   class Post(Model):
       id = IntField(primary_key=True)
       title = CharField(max_length=200)
       content = TextField()
       author = ForeignKeyField(User, related_name="posts")
       created_at = DateTimeField(auto_now_add=True)

   # Create a post
   user = await User.get(id=1)
   post = await Post.create(
       title="My First Post",
       content="Hello, world!",
       author=user
   )

   # Get user's posts
   user_posts = await user.posts.all()

   # Get post's author
   post_author = await post.author

Many-to-Many
~~~~~~~~~~~

.. code-block:: python

   from oxen.fields import ManyToManyField

   class Tag(Model):
       id = IntField(primary_key=True)
       name = CharField(max_length=50, unique=True)

   class Post(Model):
       id = IntField(primary_key=True)
       title = CharField(max_length=200)
       tags = ManyToManyField(Tag, related_name="posts")

   # Add tags to post
   post = await Post.get(id=1)
   tag = await Tag.get(name="python")
   await post.tags.add(tag)

   # Get post's tags
   post_tags = await post.tags.all()

   # Get tag's posts
   tag_posts = await tag.posts.all()

Advanced Features
----------------

Window Functions
~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen.expressions import WindowFunction

   # Rank users by score within each role
   ranked_users = await User.annotate(
       rank=WindowFunction(
           "RANK()",
           partition_by=["role"],
           order_by=["-score"]
       )
   ).values("username", "role", "score", "rank")

Common Table Expressions (CTE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen.expressions import CommonTableExpression

   # Recursive CTE for hierarchical data
   class Category(Model):
       id = IntField(primary_key=True)
       name = CharField(max_length=100)
       parent_id = ForeignKeyField("self", null=True)

   # Get all descendants of a category
   descendants_cte = CommonTableExpression(
       "descendants",
       Category.filter(id=1).union(
           Category.filter(parent_id__in=descendants_cte.values("id"))
       ),
       recursive=True
   )

   descendants = await descendants_cte.all()

Full-Text Search
~~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen.expressions import FullTextSearch

   class Article(Model):
       id = IntField(primary_key=True)
       title = CharField(max_length=200)
       content = TextField()

   # Search articles
   search_results = await Article.annotate(
       rank=FullTextSearch(
           ["title", "content"],
           "python async",
           language="english"
       )
   ).filter(rank__gt=0).order_by("-rank")

JSON Operations
~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen.fields import JSONBField
   from oxen.expressions import JSONPathQuery

   class Product(Model):
       id = IntField(primary_key=True)
       name = CharField(max_length=200)
       metadata = JSONBField()

   # Store JSON data
   product = await Product.create(
       name="Laptop",
       metadata={
           "brand": "Apple",
           "specs": {
               "cpu": "M1",
               "ram": "16GB"
           }
       }
   )

   # Query JSON fields
   apple_products = await Product.filter(
       metadata__brand="Apple"
   )

   # JSON path queries
   m1_products = await Product.filter(
       metadata__specs__cpu="M1"
   )

Array Operations
~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen.fields import ArrayField
   from oxen.expressions import ArrayOperation

   class Post(Model):
       id = IntField(primary_key=True)
       title = CharField(max_length=200)
       tags = ArrayField(element_type="text")

   # Create post with tags
   post = await Post.create(
       title="Python Tutorial",
       tags=["python", "tutorial", "beginner"]
   )

   # Find posts with specific tag
   python_posts = await Post.filter(
       ArrayOperation("tags", "contains", "python")
   )

   # Find posts with overlapping tags
   similar_posts = await Post.filter(
       ArrayOperation("tags", "overlaps", ["python", "advanced"])
   )

File and Image Operations
------------------------

File Fields
~~~~~~~~~~

.. code-block:: python

   from oxen.fields import FileField, ImageField

   class Document(Model):
       id = IntField(primary_key=True)
       title = CharField(max_length=200)
       file = FileField(upload_to="documents/")
       created_at = DateTimeField(auto_now_add=True)

   class Photo(Model):
       id = IntField(primary_key=True)
       title = CharField(max_length=200)
       image = ImageField(upload_to="photos/")
       thumbnail = ImageField(upload_to="thumbnails/")

   # Create document
   with open("document.pdf", "rb") as f:
       doc = await Document.create(
           title="My Document",
           file=f.read()
       )

   # Process image
   with open("photo.jpg", "rb") as f:
       photo = await Photo.create(
           title="My Photo",
           image=f.read()
       )

   # Create thumbnail
   thumbnail_data = await photo.image.create_thumbnail(max_size=200)
   photo.thumbnail = thumbnail_data
   await photo.save()

Direct File Operations
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen.file_operations import FileOperations

   # Initialize file operations
   file_ops = FileOperations()

   # Read file
   content = await file_ops.read_file("path/to/file.txt")

   # Write file
   await file_ops.write_file("path/to/output.txt", b"Hello, world!")

   # Image processing
   image_data = await file_ops.read_file("photo.jpg")
   resized_image = await file_ops.resize_image(image_data, 800, 600)
   await file_ops.write_file("resized_photo.jpg", resized_image)

Performance Optimization
-----------------------

Query Caching
~~~~~~~~~~~~

.. code-block:: python

   from oxen.engine import UnifiedEngine

   # Initialize engine with caching
   engine = UnifiedEngine("sqlite://:memory:")

   # Execute query with caching
   result = await engine.execute_query(
       "SELECT * FROM users WHERE is_active = ?",
       {"is_active": True},
       use_cache=True,
       cache_ttl=300  # 5 minutes
   )

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get performance statistics
   stats = engine.get_performance_stats()
   print(f"Total queries: {stats['performance_monitor']['total_queries']}")
   print(f"Average execution time: {stats['performance_monitor']['avg_execution_time']}")
   print(f"Slow queries: {stats['performance_monitor']['slow_queries']}")

   # Get cache statistics
   cache_stats = stats['query_cache']
   print(f"Cache size: {cache_stats['size']}")
   print(f"Cache hit rate: {cache_stats['hit_rate']}")

Transactions
------------

Basic Transactions
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen import transaction

   async def transfer_money(from_account, to_account, amount):
       async with transaction():
           # Deduct from source account
           from_account.balance -= amount
           await from_account.save()

           # Add to destination account
           to_account.balance += amount
           await to_account.save()

           # If any operation fails, both will be rolled back

Nested Transactions
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def complex_operation():
       async with transaction():
           # Outer transaction
           user = await User.create(username="john")
           
           async with transaction():
               # Inner transaction
               profile = await Profile.create(user=user)
               
               # If this fails, only the inner transaction is rolled back
               if some_condition:
                   raise ValueError("Something went wrong")

Signals
-------

Model Signals
~~~~~~~~~~~~

.. code-block:: python

   from oxen.signals import Signals

   @Signals.pre_save
   async def pre_save_handler(sender, instance, **kwargs):
       print(f"Saving {instance}")

   @Signals.post_save
   async def post_save_handler(sender, instance, created, **kwargs):
       if created:
           print(f"Created new {instance}")
       else:
           print(f"Updated {instance}")

   @Signals.pre_delete
   async def pre_delete_handler(sender, instance, **kwargs):
       print(f"Deleting {instance}")

Custom Signals
~~~~~~~~~~~~~

.. code-block:: python

   from oxen.signals import Signals

   # Define custom signal
   user_registered = Signals()

   @user_registered.connect
   async def send_welcome_email(user, **kwargs):
       # Send welcome email
       pass

   @user_registered.connect
   async def create_user_profile(user, **kwargs):
       # Create user profile
       pass

   # Emit signal
   user = await User.create(username="john", email="john@example.com")
   await user_registered.send(user=user)

Validation
----------

Field Validation
~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen.validators import Validator
   from oxen.fields import CharField

   class EmailValidator(Validator):
       def __call__(self, value):
           if '@' not in value:
               raise ValidationError("Invalid email format")
           return value

   class User(Model):
       id = IntField(primary_key=True)
       email = CharField(max_length=100, validators=[EmailValidator()])

Model Validation
~~~~~~~~~~~~~~~

.. code-block:: python

   class User(Model):
       id = IntField(primary_key=True)
       username = CharField(max_length=50)
       email = CharField(max_length=100)

       async def clean(self):
           # Custom validation logic
           if await User.filter(username=self.username).exists():
               raise ValidationError("Username already exists")

           if await User.filter(email=self.email).exists():
               raise ValidationError("Email already exists")

Migrations
----------

Creating Migrations
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen.migrations import Migration

   class CreateUserTable(Migration):
       async def up(self):
           await self.execute("""
               CREATE TABLE users (
                   id INTEGER PRIMARY KEY,
                   username VARCHAR(50) UNIQUE NOT NULL,
                   email VARCHAR(100) UNIQUE NOT NULL,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           """)

       async def down(self):
           await self.execute("DROP TABLE users")

Running Migrations
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from oxen.migrations import run_migrations

   # Run all pending migrations
   await run_migrations()

   # Run specific migration
   await run_migrations("CreateUserTable")

   # Rollback last migration
   await run_migrations(rollback=True)

Best Practices
-------------

Model Design
~~~~~~~~~~~

.. code-block:: python

   class User(Model):
       # Use meaningful field names
       id = IntField(primary_key=True)
       username = CharField(max_length=50, unique=True)
       email = CharField(max_length=100, unique=True)
       
       # Add indexes for frequently queried fields
       class Meta:
           indexes = [
               ("username",),
               ("email",),
               ("created_at",)
           ]

Query Optimization
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use select_related for foreign keys
   posts = await Post.select_related("author").all()

   # Use prefetch_related for many-to-many
   posts = await Post.prefetch_related("tags").all()

   # Use only() to select specific fields
   users = await User.only("id", "username").all()

   # Use defer() to exclude specific fields
   users = await User.defer("password_hash").all()

Error Handling
~~~~~~~~~~~~~

.. code-block:: python

   from oxen.exceptions import DoesNotExist, ValidationError

   try:
       user = await User.get(username="john")
   except DoesNotExist:
       print("User not found")
   except ValidationError as e:
       print(f"Validation error: {e}")

Connection Management
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   from oxen import connect, disconnect

   async def main():
       try:
           await connect("postgresql://user:pass@localhost/db")
           # Your application code
       finally:
           await disconnect()

   if __name__ == "__main__":
       asyncio.run(main()) 