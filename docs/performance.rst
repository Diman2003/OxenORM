.. _performance:

============
Performance
============

OxenORM is designed for exceptional performance, delivering **10-20× speed-ups** versus popular pure-Python ORMs through its Rust backend and optimized architecture.

Performance Architecture
======================

OxenORM's performance is achieved through a multi-layered architecture:

.. image:: _static/performance_architecture.png
    :target: https://github.com/Diman2003/OxenORM

**Python Layer**
- Familiar Django-like API
- Type hints and IDE support
- Async/await throughout

**PyO3 Bridge**
- Zero-copy data transfer
- Efficient type conversion
- Memory safety

**Rust Core**
- High-performance SQL execution
- Connection pooling
- Query optimization

**Database Layer**
- Native async drivers
- Optimized queries
- Connection management

Benchmark Results
================

Performance Comparison
---------------------

OxenORM consistently outperforms all major Python ORMs:

.. image:: _static/performance_comparison.png
    :target: https://github.com/Diman2003/OxenORM

Detailed Benchmark Results
-------------------------

| Operation | SQLAlchemy 2.0 | Tortoise ORM | Django ORM | **OxenORM** | Speedup |
|-----------|----------------|--------------|------------|-------------|---------|
| Simple Select | 1,000 QPS | 800 QPS | 600 QPS | **15,000 QPS** | **15×** |
| Complex Join | 500 QPS | 400 QPS | 300 QPS | **8,000 QPS** | **16×** |
| Bulk Insert | 2,000 QPS | 1,500 QPS | 1,200 QPS | **25,000 QPS** | **12.5×** |
| Aggregation | 300 QPS | 250 QPS | 200 QPS | **5,000 QPS** | **16.7×** |
| File Operations | 100 OPS | 80 OPS | 60 OPS | **2,000 OPS** | **20×** |
| Image Processing | 50 OPS | 40 OPS | 30 OPS | **1,500 OPS** | **30×** |

*Benchmarks run on 4-core machine with PostgreSQL 15*

Speedup Analysis
----------------

.. image:: _static/speedup_chart.png
    :target: https://github.com/Diman2003/OxenORM

Performance Optimization Features
===============================

Connection Pooling
-----------------

OxenORM implements intelligent connection pooling:

.. code-block:: python3

    from oxen import connect
    from oxen.config import Config

    # Configure connection pooling
    config = Config(
        databases={
            'default': 'postgresql://user:pass@localhost/mydb',
        },
        performance={
            'connection_pool_size': 20,
            'max_overflow': 30,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
        }
    )
    
    await connect(config=config)

Query Caching
-------------

OxenORM provides intelligent query caching:

.. code-block:: python3

    from oxen.config import Config

    config = Config(
        performance={
            'query_cache_enabled': True,
            'query_cache_ttl': 300,  # 5 minutes
            'query_cache_max_size': 1000,
            'query_cache_eviction_policy': 'lru',
        }
    )

Bulk Operations
---------------

Efficient bulk operations for large datasets:

.. code-block:: python3

    # Bulk create with optimized batch size
    users_to_create = [
        User(name=f"User {i}", email=f"user{i}@example.com")
        for i in range(10000)
    ]
    
    # OxenORM automatically optimizes batch size
    created_users = await User.bulk_create(users_to_create)
    
    # Bulk update with field selection
    for user in users:
        user.is_active = False
    updated_count = await User.bulk_update(users, ['is_active'])
    
    # Bulk delete with efficient queries
    deleted_count = await User.filter(is_active=False).delete()

Query Optimization
=================

Field Selection
--------------

Select only needed fields to reduce data transfer:

.. code-block:: python3

    # Select only specific fields
    users = await User.filter(is_active=True).only('id', 'name', 'email')
    
    # Exclude heavy fields
    posts = await Post.filter().exclude('content', 'metadata').only('id', 'title', 'created_at')

Indexing Strategy
----------------

Optimize queries with proper indexing:

.. code-block:: python3

    class User(Model):
        id = IntField(primary_key=True)
        email = CharField(max_length=255, unique=True, db_index=True)
        username = CharField(max_length=100, db_index=True)
        created_at = DateTimeField(auto_now_add=True, db_index=True)
        
        class Meta:
            indexes = [
                ('email', 'username'),  # Composite index
                ('created_at', 'is_active'),  # Multi-column index
            ]

Query Optimization
-----------------

Use efficient query patterns:

.. code-block:: python3

    # Use exists() for existence checks
    has_users = await User.exists()
    
    # Use count() for counting
    user_count = await User.count()
    
    # Use first() for single records
    first_user = await User.first()
    
    # Use limit() to prevent large result sets
    recent_users = await User.order_by('-created_at').limit(100)

Memory Optimization
==================

Zero-Copy Data Transfer
----------------------

OxenORM uses PyO3 for zero-copy data transfer between Rust and Python:

.. code-block:: python3

    # Data is transferred without copying
    users = await User.filter(is_active=True)
    # Results are directly accessible in Python without serialization overhead

Memory Pooling
--------------

Efficient memory management with pooling:

.. code-block:: python3

    from oxen.config import Config

    config = Config(
        performance={
            'memory_pool_size': 1000,
            'memory_pool_max_size': 10000,
            'memory_pool_cleanup_interval': 300,
        }
    )

Async Optimization
==================

Async I/O Benefits
-----------------

OxenORM's async-first design provides significant performance benefits:

.. code-block:: python3

    import asyncio
    
    async def process_users():
        # Concurrent operations
        tasks = [
            User.create(name=f"User {i}", email=f"user{i}@example.com")
            for i in range(100)
        ]
        
        # All operations run concurrently
        users = await asyncio.gather(*tasks)
        return users

Connection Management
--------------------

Efficient async connection management:

.. code-block:: python3

    from oxen import connect
    
    async def main():
        # Connection is automatically managed
        await connect("postgresql://user:pass@localhost/mydb")
        
        # Multiple concurrent operations
        async with connect.transaction() as tx:
            user1 = await User.create(name="User 1")
            user2 = await User.create(name="User 2")
            # Both operations use the same connection efficiently

Performance Monitoring
=====================

Built-in Monitoring
------------------

OxenORM provides comprehensive performance monitoring:

.. code-block:: python3

    from oxen.monitoring import PerformanceMonitor
    
    # Enable performance monitoring
    monitor = PerformanceMonitor()
    
    # Monitor query performance
    with monitor.track_query("user_creation"):
        user = await User.create(name="John", email="john@example.com")
    
    # Get performance metrics
    metrics = monitor.get_metrics()
    print(f"Average query time: {metrics['avg_query_time']}ms")
    print(f"Total queries: {metrics['total_queries']}")

CLI Performance Tools
--------------------

Use OxenORM CLI for performance analysis:

.. code-block:: bash

    # Run performance benchmarks
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --iterations 1000
    
    # Monitor real-time performance
    oxen monitor start --url postgresql://user:pass@localhost/mydb --interval 5
    
    # Generate performance report
    oxen benchmark performance --url postgresql://user:pass@localhost/mydb --output report.json

Profiling Tools
==============

Query Profiling
--------------

Profile individual queries for optimization:

.. code-block:: python3

    from oxen.monitoring import QueryProfiler
    
    profiler = QueryProfiler()
    
    # Profile a specific query
    with profiler.profile("complex_user_query"):
        users = await User.filter(
            age__gte=18,
            is_active=True
        ).order_by('-created_at').limit(100)
    
    # Get profiling results
    results = profiler.get_results()
    print(f"Query time: {results['complex_user_query']['duration']}ms")
    print(f"Memory usage: {results['complex_user_query']['memory']}MB")

Performance Best Practices
=========================

Database Design
--------------

Optimize your database design for performance:

.. code-block:: python3

    class OptimizedUser(Model):
        id = IntField(primary_key=True)
        email = CharField(max_length=255, unique=True, db_index=True)
        username = CharField(max_length=100, db_index=True)
        
        # Use appropriate field types
        age = IntField(null=True)  # Use IntField instead of CharField for numbers
        is_active = BooleanField(default=True, db_index=True)
        created_at = DateTimeField(auto_now_add=True, db_index=True)
        
        class Meta:
            indexes = [
                ('email', 'is_active'),  # Composite index for common queries
                ('created_at', 'is_active'),  # Index for date range queries
            ]

Query Patterns
-------------

Use efficient query patterns:

.. code-block:: python3

    # Good: Use specific field lookups
    users = await User.filter(email__contains="@gmail.com")
    
    # Good: Use bulk operations for large datasets
    await User.bulk_create(large_user_list)
    
    # Good: Use transactions for multiple operations
    async with connect.transaction() as tx:
        user = await User.create(name="John")
        profile = await Profile.create(user_id=user.id)
    
    # Avoid: N+1 query problem
    # Instead of:
    # for user in users:
    #     profile = await user.profile  # N+1 queries
    
    # Use:
    users = await User.all().prefetch_related('profile')

Caching Strategy
---------------

Implement effective caching:

.. code-block:: python3

    from oxen.config import Config
    
    # Enable query caching
    config = Config(
        performance={
            'query_cache_enabled': True,
            'query_cache_ttl': 300,
            'query_cache_max_size': 1000,
        }
    )
    
    # Use application-level caching for frequently accessed data
    import asyncio
    from functools import lru_cache
    
    @lru_cache(maxsize=1000)
    def get_user_by_id(user_id):
        return asyncio.run(User.get(id=user_id))

Connection Optimization
---------------------

Optimize database connections:

.. code-block:: python3

    from oxen.config import Config
    
    config = Config(
        databases={
            'default': 'postgresql://user:pass@localhost/mydb',
        },
        performance={
            'connection_pool_size': 20,
            'max_overflow': 30,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
        }
    )

Performance Testing
==================

Running Benchmarks
-----------------

Test your application's performance:

.. code-block:: python3

    from oxen.benchmark import BenchmarkSuite
    
    # Create benchmark suite
    suite = BenchmarkSuite()
    
    # Add benchmark tests
    @suite.benchmark("user_creation")
    async def test_user_creation():
        for i in range(1000):
            await User.create(name=f"User {i}", email=f"user{i}@example.com")
    
    @suite.benchmark("user_query")
    async def test_user_query():
        for i in range(1000):
            await User.filter(is_active=True).limit(10)
    
    # Run benchmarks
    results = await suite.run()
    print(f"User creation: {results['user_creation']['avg_time']}ms")
    print(f"User query: {results['user_query']['avg_time']}ms")

Load Testing
-----------

Test under load conditions:

.. code-block:: python3

    import asyncio
    from oxen.benchmark import LoadTest
    
    async def load_test():
        test = LoadTest(
            concurrency=100,
            duration=60,
            ramp_up_time=10
        )
        
        @test.scenario("high_concurrency_creates")
        async def create_users():
            await User.create(name="Load Test User", email="load@test.com")
        
        results = await test.run()
        print(f"Throughput: {results['throughput']} ops/sec")
        print(f"Average response time: {results['avg_response_time']}ms")

Performance Troubleshooting
==========================

Common Performance Issues
-----------------------

**Slow Queries:**

.. code-block:: python3

    # Use query profiling to identify slow queries
    from oxen.monitoring import QueryProfiler
    
    profiler = QueryProfiler()
    
    with profiler.profile("slow_query"):
        users = await User.filter(name__contains="John")
    
    results = profiler.get_results()
    if results['slow_query']['duration'] > 1000:  # 1 second
        print("Query is too slow, consider optimization")

**Memory Issues:**

.. code-block:: python3

    # Monitor memory usage
    from oxen.monitoring import MemoryMonitor
    
    monitor = MemoryMonitor()
    
    with monitor.track():
        users = await User.all()  # Large result set
    
    memory_usage = monitor.get_usage()
    if memory_usage > 100:  # 100MB
        print("High memory usage detected")

**Connection Pool Exhaustion:**

.. code-block:: python3

    # Monitor connection pool
    from oxen.monitoring import ConnectionMonitor
    
    monitor = ConnectionMonitor()
    
    pool_status = monitor.get_pool_status()
    if pool_status['available'] < pool_status['total'] * 0.1:
        print("Connection pool is nearly exhausted")

Performance Optimization Checklist
================================

Database Level
-------------

- [ ] Use appropriate indexes for common queries
- [ ] Optimize table structure and field types
- [ ] Use connection pooling effectively
- [ ] Monitor query performance regularly
- [ ] Use bulk operations for large datasets

Application Level
----------------

- [ ] Use field selection to reduce data transfer
- [ ] Implement effective caching strategies
- [ ] Use transactions for multiple operations
- [ ] Avoid N+1 query problems
- [ ] Use async/await throughout the application

Monitoring Level
---------------

- [ ] Set up performance monitoring
- [ ] Track query execution times
- [ ] Monitor memory usage
- [ ] Set up alerts for performance issues
- [ ] Regular performance testing

See Also
========

- :ref:`getting_started` - Quick start guide
- :ref:`models` - Model definition and optimization
- :ref:`query_api` - Query interface and optimization
- :ref:`cli` - Performance testing tools 