API Reference
============

This document provides a comprehensive reference for the OxenORM API.

Models
------

.. class:: Model

   Base class for all OxenORM models. Extends Tortoise's Model with Rust backend integration.

   **Example:**

   .. code-block:: python

      from oxen import Model
      from oxen.fields import IntField, CharField

      class User(Model):
          id = IntField(primary_key=True)
          username = CharField(max_length=50, unique=True)
          email = CharField(max_length=100, unique=True)

   **Class Methods:**

   .. method:: create(**kwargs) -> Model

      Create and save a new model instance.

      :param kwargs: Field values for the new instance
      :return: The created model instance
      :raises: ValidationError, IntegrityError

      **Example:**

      .. code-block:: python

         user = await User.create(
             username="john_doe",
             email="john@example.com"
         )

   .. method:: get(**kwargs) -> Model

      Get a single model instance by filter criteria.

      :param kwargs: Filter criteria
      :return: The matching model instance
      :raises: DoesNotExist, MultipleObjectsReturned

      **Example:**

      .. code-block:: python

         user = await User.get(username="john_doe")

   .. method:: filter(**kwargs) -> QuerySet

      Filter model instances by criteria.

      :param kwargs: Filter criteria
      :return: QuerySet with filtered results

      **Example:**

      .. code-block:: python

         active_users = await User.filter(is_active=True)

   .. method:: all() -> QuerySet

      Get all model instances.

      :return: QuerySet with all instances

      **Example:**

      .. code-block:: python

         all_users = await User.all()

   .. method:: count() -> int

      Count the number of model instances.

      :return: Number of instances

      **Example:**

      .. code-block:: python

         user_count = await User.count()

   **Instance Methods:**

   .. method:: save() -> None

      Save the model instance to the database.

      :raises: ValidationError, IntegrityError

      **Example:**

      .. code-block:: python

         user.username = "new_username"
         await user.save()

   .. method:: delete() -> None

      Delete the model instance from the database.

      :raises: OperationalError

      **Example:**

      .. code-block:: python

         await user.delete()

   .. method:: refresh_from_db() -> None

      Refresh the model instance from the database.

      :raises: DoesNotExist

      **Example:**

      .. code-block:: python

         await user.refresh_from_db()

Fields
------

Base Field
~~~~~~~~~~

.. class:: Field

   Abstract base class for all field types.

   **Parameters:**

   - **primary_key** (bool): Whether this field is the primary key
   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default**: Default value for this field
   - **description** (str): Field description for documentation

Data Fields
~~~~~~~~~~

.. class:: IntField

   Integer field type.

   **Parameters:**

   - **primary_key** (bool): Whether this field is the primary key
   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default** (int): Default value
   - **auto_increment** (bool): Whether this field auto-increments

   **Example:**

   .. code-block:: python

      id = IntField(primary_key=True, auto_increment=True)
      age = IntField(default=18)

.. class:: CharField

   Character field type.

   **Parameters:**

   - **max_length** (int): Maximum length of the string
   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default** (str): Default value

   **Example:**

   .. code-block:: python

      username = CharField(max_length=50, unique=True)
      name = CharField(max_length=100, default="")

.. class:: TextField

   Text field type for long strings.

   **Parameters:**

   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default** (str): Default value

   **Example:**

   .. code-block:: python

      bio = TextField(null=True)
      content = TextField(default="")

.. class:: BooleanField

   Boolean field type.

   **Parameters:**

   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default** (bool): Default value

   **Example:**

   .. code-block:: python

      is_active = BooleanField(default=True)
      is_verified = BooleanField(default=False)

.. class:: DateTimeField

   DateTime field type.

   **Parameters:**

   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default**: Default value
   - **auto_now_add** (bool): Set to current time on creation
   - **auto_now** (bool): Set to current time on save

   **Example:**

   .. code-block:: python

      created_at = DateTimeField(auto_now_add=True)
      updated_at = DateTimeField(auto_now=True)

.. class:: DateField

   Date field type.

   **Parameters:**

   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default**: Default value
   - **auto_now_add** (bool): Set to current date on creation
   - **auto_now** (bool): Set to current date on save

   **Example:**

   .. code-block:: python

      birth_date = DateField(null=True)
      created_date = DateField(auto_now_add=True)

.. class:: TimeField

   Time field type.

   **Parameters:**

   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default**: Default value

   **Example:**

   .. code-block:: python

      start_time = TimeField()
      end_time = TimeField(null=True)

.. class:: DecimalField

   Decimal field type for precise numeric values.

   **Parameters:**

   - **max_digits** (int): Maximum number of digits
   - **decimal_places** (int): Number of decimal places
   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default**: Default value

   **Example:**

   .. code-block:: python

      price = DecimalField(max_digits=10, decimal_places=2)
      rating = DecimalField(max_digits=3, decimal_places=2, default=0.0)

.. class:: FloatField

   Float field type.

   **Parameters:**

   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default** (float): Default value

   **Example:**

   .. code-block:: python

      score = FloatField(default=0.0)
      temperature = FloatField(null=True)

.. class:: JSONField

   JSON field type for storing structured data.

   **Parameters:**

   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default**: Default value

   **Example:**

   .. code-block:: python

      metadata = JSONField(default=dict)
      settings = JSONField(null=True)

.. class:: UUIDField

   UUID field type.

   **Parameters:**

   - **primary_key** (bool): Whether this field is the primary key
   - **unique** (bool): Whether this field must be unique
   - **null** (bool): Whether this field can be null
   - **default**: Default value

   **Example:**

   .. code-block:: python

      id = UUIDField(primary_key=True, default=uuid4)
      reference = UUIDField(unique=True)

Relational Fields
~~~~~~~~~~~~~~~~

.. class:: ForeignKeyField

   Foreign key field for many-to-one relationships.

   **Parameters:**

   - **to** (Model): The related model class
   - **related_name** (str): Name for the reverse relationship
   - **null** (bool): Whether this field can be null
   - **on_delete** (str): Action on delete (CASCADE, SET_NULL, etc.)

   **Example:**

   .. code-block:: python

      author = ForeignKeyField(User, related_name="posts")
      category = ForeignKeyField(Category, related_name="products")

.. class:: OneToOneField

   One-to-one relationship field.

   **Parameters:**

   - **to** (Model): The related model class
   - **related_name** (str): Name for the reverse relationship
   - **null** (bool): Whether this field can be null
   - **on_delete** (str): Action on delete

   **Example:**

   .. code-block:: python

      profile = OneToOneField(UserProfile, related_name="user")

.. class:: ManyToManyField

   Many-to-many relationship field.

   **Parameters:**

   - **to** (Model): The related model class
   - **related_name** (str): Name for the reverse relationship
   - **through** (str): Custom through table name

   **Example:**

   .. code-block:: python

      tags = ManyToManyField(Tag, related_name="posts")
      followers = ManyToManyField(User, related_name="following")

QuerySet
--------

.. class:: QuerySet

   QuerySet for building and executing database queries.

   **Methods:**

   .. method:: filter(**kwargs) -> QuerySet

      Filter the queryset by criteria.

      :param kwargs: Filter criteria
      :return: Filtered QuerySet

      **Example:**

      .. code-block:: python

         active_users = User.filter(is_active=True)
         recent_posts = Post.filter(created_at__gte=week_ago)

   .. method:: exclude(**kwargs) -> QuerySet

      Exclude records matching criteria.

      :param kwargs: Exclusion criteria
      :return: Filtered QuerySet

      **Example:**

      .. code-block:: python

         non_admin_users = User.exclude(is_admin=True)

   .. method:: order_by(*fields) -> QuerySet

      Order the queryset by fields.

      :param fields: Field names to order by (prefix with - for descending)
      :return: Ordered QuerySet

      **Example:**

      .. code-block:: python

         users_by_name = User.order_by("username")
         recent_posts = Post.order_by("-created_at")

   .. method:: limit(limit) -> QuerySet

      Limit the number of results.

      :param limit: Maximum number of results
      :return: Limited QuerySet

      **Example:**

      .. code-block:: python

         top_users = User.order_by("-score").limit(10)

   .. method:: offset(offset) -> QuerySet

      Skip a number of results.

      :param offset: Number of results to skip
      :return: Offset QuerySet

      **Example:**

      .. code-block:: python

         page_2 = User.limit(20).offset(20)

   .. method:: distinct() -> QuerySet

      Return distinct results.

      :return: Distinct QuerySet

      **Example:**

      .. code-block:: python

         unique_categories = Post.values("category").distinct()

   .. method:: values(*fields) -> List[Dict]

      Return values as dictionaries.

      :param fields: Field names to include
      :return: List of dictionaries

      **Example:**

      .. code-block:: python

         user_data = User.values("id", "username", "email")

   .. method:: values_list(*fields, flat=False) -> List

      Return values as lists or tuples.

      :param fields: Field names to include
      :param flat: Whether to flatten single-field results
      :return: List of values

      **Example:**

      .. code-block:: python

         usernames = User.values_list("username", flat=True)
         user_tuples = User.values_list("id", "username")

   .. method:: count() -> int

      Count the number of results.

      :return: Number of results

      **Example:**

      .. code-block:: python

         user_count = User.filter(is_active=True).count()

   .. method:: exists() -> bool

      Check if any results exist.

      :return: True if results exist, False otherwise

      **Example:**

      .. code-block:: python

         has_users = User.exists()

   .. method:: first() -> Model | None

      Get the first result.

      :return: First model instance or None

      **Example:**

      .. code-block:: python

         first_user = User.first()

   .. method:: last() -> Model | None

      Get the last result.

      :return: Last model instance or None

      **Example:**

      .. code-block:: python

         last_user = User.order_by("-created_at").last()

   .. method:: get(**kwargs) -> Model

      Get a single result.

      :param kwargs: Filter criteria
      :return: Model instance
      :raises: DoesNotExist, MultipleObjectsReturned

      **Example:**

      .. code-block:: python

         user = User.get(username="john_doe")

   .. method:: create(**kwargs) -> Model

      Create and save a new instance.

      :param kwargs: Field values
      :return: Created model instance

      **Example:**

      .. code-block:: python

         user = User.create(username="newuser", email="new@example.com")

   .. method:: bulk_create(objects, batch_size=None) -> List[Model]

      Bulk create multiple instances.

      :param objects: List of model instances
      :param batch_size: Batch size for processing
      :return: List of created instances

      **Example:**

      .. code-block:: python

         users = [User(username=f"user{i}") for i in range(100)]
         created_users = User.bulk_create(users)

   .. method:: update(**kwargs) -> int

      Update all instances in the queryset.

      :param kwargs: Field values to update
      :return: Number of updated instances

      **Example:**

      .. code-block:: python

         updated_count = User.filter(is_active=False).update(is_active=True)

   .. method:: delete() -> int

      Delete all instances in the queryset.

      :return: Number of deleted instances

      **Example:**

      .. code-block:: python

         deleted_count = User.filter(is_active=False).delete()

Database Connection
------------------

.. function:: init_db(connections, default_connection=None, **kwargs) -> None

   Initialize database connections.

   :param connections: Dictionary mapping connection names to connection strings
   :param default_connection: Name of the default connection
   :param kwargs: Additional configuration options

   **Example:**

   .. code-block:: python

      await init_db({
          'default': 'postgresql://user:pass@localhost/mydb',
          'readonly': 'postgresql://user:pass@readonly/mydb'
      }, default_connection='default')

.. function:: close_db() -> None

   Close all database connections.

   **Example:**

   .. code-block:: python

      await close_db()

.. function:: get_connection(name=None) -> OxenEngine

   Get a database connection by name.

   :param name: Connection name (uses default if not specified)
   :return: OxenEngine instance

   **Example:**

   .. code-block:: python

      engine = get_connection('readonly')

Transactions
------------

.. function:: transaction() -> AsyncContextManager

   Transaction context manager.

   **Example:**

   .. code-block:: python

      from oxen import transaction

      async with transaction():
          user = await User.create(username="john", email="john@example.com")
          post = await Post.create(title="My Post", author=user)

Exceptions
----------

.. exception:: OxenError

   Base exception for all OxenORM errors.

.. exception:: ConfigurationError

   Raised when there's a configuration error.

.. exception:: ValidationError

   Raised when field validation fails.

.. exception:: IntegrityError

   Raised when database integrity constraints are violated.

.. exception:: DoesNotExist

   Raised when a requested object doesn't exist.

.. exception:: MultipleObjectsReturned

   Raised when multiple objects are returned when only one was expected.

.. exception:: OperationalError

   Raised when a database operation fails.

.. exception:: ConnectionError

   Raised when there's a connection error.

.. exception:: MigrationError

   Raised when a migration operation fails.

Query Expressions
-----------------

.. class:: Q

   Query expression for building complex queries.

   **Methods:**

   .. method:: __and__(other) -> Q

      Combine queries with AND.

      **Example:**

      .. code-block:: python

         from oxen import Q
         query = Q(is_active=True) & Q(age__gte=18)

   .. method:: __or__(other) -> Q

      Combine queries with OR.

      **Example:**

      .. code-block:: python

         query = Q(is_admin=True) | Q(is_moderator=True)

   .. method:: __invert__() -> Q

      Negate a query.

      **Example:**

      .. code-block:: python

         query = ~Q(is_active=False)  # Equivalent to is_active=True

   **Usage:**

   .. code-block:: python

      from oxen import Q

      # Complex queries
      users = await User.filter(
          Q(is_active=True) & (Q(age__gte=18) | Q(is_admin=True))
      )

      # Field lookups
      recent_posts = await Post.filter(
          Q(created_at__gte=week_ago) & Q(published=True)
      )

Field Lookups
------------

OxenORM supports various field lookups for filtering:

- **exact**: Exact match (default)
- **iexact**: Case-insensitive exact match
- **contains**: Contains substring
- **icontains**: Case-insensitive contains
- **startswith**: Starts with substring
- **istartswith**: Case-insensitive starts with
- **endswith**: Ends with substring
- **iendswith**: Case-insensitive ends with
- **in**: Value is in list
- **gt**: Greater than
- **gte**: Greater than or equal
- **lt**: Less than
- **lte**: Less than or equal
- **isnull**: Is null or not null

**Examples:**

.. code-block:: python

   # Exact match
   user = await User.get(username="john")

   # Case-insensitive contains
   users = await User.filter(username__icontains="john")

   # Greater than
   adults = await User.filter(age__gte=18)

   # In list
   admins = await User.filter(role__in=["admin", "moderator"])

   # Is null
   users_without_bio = await User.filter(bio__isnull=True)

   # Not null
   users_with_bio = await User.filter(bio__isnull=False) 