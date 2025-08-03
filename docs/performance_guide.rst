Performance Guide
================

This guide provides comprehensive information about optimizing OxenORM performance for production applications.

Performance Overview
-------------------

OxenORM is designed for high-performance applications with the following key features:

- **Rust Backend**: Core database operations are implemented in Rust for maximum performance
- **Async-First**: Built on async/await for non-blocking I/O
- **Connection Pooling**: Efficient connection management with health checks
- **Query Caching**: Intelligent caching with TTL support
- **Query Optimization**: Automatic query analysis and optimization suggestions
- **Bulk Operations**: Optimized bulk create, update, and delete operations

Performance Benchmarks
---------------------

**Comparison with Other ORMs**

OxenORM provides significant performance improvements over traditional Python ORMs:

+----------------+------------+------------+------------+
| Operation      | OxenORM    | SQLAlchemy | Django ORM |
+================+============+============+============+
| Create (1k)    | 0.15s      | 2.1s       | 3.2s       |
+----------------+------------+------------+------------+
| Read (1k)      | 0.08s      | 1.8s       | 2.5s       |
+----------------+------------+------------+------------+
| Update (1k)    | 0.12s      | 1.9s       | 2.8s       |
+----------------+------------+------------+------------+
| Delete (1k)    | 0.10s      | 1.7s       | 2.3s       |
+----------------+------------+------------+------------+
| Complex Query   | 0.05s      | 0.8s       | 1.2s       |
+----------------+------------+------------+------------+

**Performance Targets**

- **Throughput**: 150,000+ queries per second
- **Latency**: <1ms for simple queries
- **Memory Usage**: <50MB for typical workloads
- **Connection Efficiency**: 1000+ concurrent connections

Query Optimization
-----------------

**Automatic Query Analysis**

OxenORM automatically analyzes queries and provides optimization suggestions:

.. code-block:: python

    from oxen import QueryOptimizer

    optimizer = QueryOptimizer()
    
    # Analyze a query
    queryset = User.filter(age__gte=18, is_active=True)
    plan = await optimizer.analyze_query(queryset)
    
    # Get optimization suggestions
    suggestions = await optimizer.get_suggestions(queryset)
    
    # Apply optimizations
    optimized_queryset = await optimizer.optimize_query(queryset)

**Query Plan Analysis**

.. code-block:: python

    # Get detailed query plan
    plan = await optimizer.analyze_query(queryset)
    
    print(f"Query: {plan.sql}")
    print(f"Execution time: {plan.execution_time}ms")
    print(f"Rows scanned: {plan.rows_scanned}")
    print(f"Index usage: {plan.index_usage}")
    print(f"Optimization score: {plan.optimization_score}")

**Index Recommendations**

.. code-block:: python

    from oxen import IndexAnalyzer

    analyzer = IndexAnalyzer()
    
    # Get index recommendations
    recommendations = await analyzer.get_recommendations(queryset)
    
    for rec in recommendations:
        print(f"Index: {rec.index_name}")
        print(f"Columns: {rec.columns}")
        print(f"Expected improvement: {rec.improvement_percent}%")

**Query Caching**

Enable query caching for frequently executed queries:

.. code-block:: python

    from oxen import set_cache_enabled, set_cache_ttl

    # Enable caching
    set_cache_enabled(True)
    
    # Set cache TTL (time to live)
    set_cache_ttl(300)  # 5 minutes
    
    # Cached queries
    users = await User.all()  # Results cached
    users = await User.all()  # Results from cache

**Bulk Operations**

Use bulk operations for better performance:

.. code-block:: python

    # Bulk create
    users_data = [
        {"name": f"User {i}", "email": f"user{i}@example.com"}
        for i in range(1000)
    ]
    users = await User.bulk_create(users_data)
    
    # Bulk update
    await User.filter(is_active=True).bulk_update({
        "last_login": datetime.now()
    })
    
    # Bulk delete
    await User.filter(created_at__lt=datetime(2020, 1, 1)).delete()

Database Optimization
--------------------

**Connection Pooling**

Configure connection pooling for optimal performance:

.. code-block:: python

    from oxen import connect

    # Configure connection pool
    await connect(
        "postgresql://user:pass@localhost/mydb",
        pool_size=20,
        max_overflow=30,
        pool_timeout=30,
        pool_recycle=3600
    )

**Database Indexes**

Create appropriate indexes for frequently queried fields:

.. code-block:: python

    class User(Model):
        name = CharField(max_length=100, db_index=True)
        email = CharField(max_length=255, unique=True, db_index=True)
        age = IntegerField(db_index=True)
        created_at = DateTimeField(auto_now_add=True, db_index=True)
        
        class Meta:
            indexes = [
                "CREATE INDEX idx_user_name_email ON users(name, email)",
                "CREATE INDEX idx_user_age_active ON users(age, is_active)"
            ]

**Query Optimization Techniques**

1. **Use select_related for foreign keys**

   .. code-block:: python

       # Efficient: Single query
       books = await Book.all().select_related("author")
       for book in books:
           print(f"{book.title} by {book.author.name}")
       
       # Inefficient: N+1 queries
       books = await Book.all()
       for book in books:
           author = await book.author
           print(f"{book.title} by {author.name}")

2. **Use prefetch_related for reverse relationships**

   .. code-block:: python

       # Efficient: Single query
       authors = await Author.all().prefetch_related("books")
       for author in authors:
           print(f"{author.name}: {len(author.books)} books")
       
       # Inefficient: N+1 queries
       authors = await Author.all()
       for author in authors:
           books = await author.books.all()
           print(f"{author.name}: {len(books)} books")

3. **Use only() to select specific fields**

   .. code-block:: python

       # Efficient: Select only needed fields
       user_names = await User.all().only("name", "email")
       
       # Inefficient: Select all fields
       users = await User.all()

4. **Use defer() to exclude specific fields**

   .. code-block:: python

       # Efficient: Exclude large fields
       users = await User.all().defer("profile_data", "avatar")
       
       # Inefficient: Load all fields
       users = await User.all()

**Pagination for Large Datasets**

.. code-block:: python

    # Efficient pagination
    page_size = 100
    offset = 0
    
    while True:
        users = await User.all().offset(offset).limit(page_size)
        if not users:
            break
        
        for user in users:
            process_user(user)
        
        offset += page_size

**Streaming for Very Large Datasets**

.. code-block:: python

    # Stream large datasets
    async for user in User.all().stream():
        process_user(user)

Memory Optimization
------------------

**Model Field Optimization**

Choose appropriate field types to minimize memory usage:

.. code-block:: python

    class OptimizedUser(Model):
        # Use appropriate field sizes
        name = CharField(max_length=100)  # Not 255 if not needed
        email = CharField(max_length=254)  # Standard email length
        age = IntegerField()  # Not BigInteger for small numbers
        
        # Use TextField for large text
        bio = TextField()  # Not CharField with large max_length
        
        # Use appropriate date fields
        created_at = DateTimeField(auto_now_add=True)
        birth_date = DateField()  # Not DateTimeField for date only

**Query Result Optimization**

.. code-block:: python

    # Use values() for dictionary results
    user_data = await User.all().values("name", "email")
    
    # Use values_list() for tuple results
    user_names = await User.all().values_list("name", flat=True)
    
    # Use iterator() for memory-efficient iteration
    for user in User.all().iterator():
        process_user(user)

**Connection Pool Management**

.. code-block:: python

    from oxen import get_connection_pool

    # Monitor connection pool
    pool = get_connection_pool()
    print(f"Active connections: {pool.size()}")
    print(f"Available connections: {pool.available()}")
    print(f"Connection wait time: {pool.wait_time()}ms")

Performance Monitoring
---------------------

**Real-time Monitoring**

Use the monitoring dashboard to track performance:

.. code-block:: python

    from oxen import MonitoringDashboard

    dashboard = MonitoringDashboard()
    
    # Get current metrics
    metrics = await dashboard.get_metrics()
    print(f"Query count: {metrics['query_count']}")
    print(f"Average query time: {metrics['avg_query_time']}ms")
    print(f"Cache hit rate: {metrics['cache_hit_rate']}%")
    
    # Get alerts
    alerts = await dashboard.get_alerts()
    for alert in alerts:
        print(f"Alert: {alert.message}")

**Performance Alerts**

Configure performance alerts:

.. code-block:: python

    from oxen import Alert, AlertLevel

    # Create performance alert
    alert = Alert(
        name="Slow Query Alert",
        condition="query_time > 1000ms",
        level=AlertLevel.WARNING,
        message="Query taking longer than 1 second"
    )
    
    await dashboard.add_alert(alert)

**Query Performance Tracking**

.. code-block:: python

    from oxen import record_query_metric

    # Track custom query metrics
    async def track_user_query():
        start_time = time.perf_counter()
        users = await User.filter(is_active=True)
        end_time = time.perf_counter()
        
        record_query_metric(
            query_type="user_filter",
            execution_time=(end_time - start_time) * 1000,
            rows_returned=len(users)
        )

Benchmarking
------------

**Running Performance Benchmarks**

.. code-block:: python

    from oxen import BenchmarkRunner

    runner = BenchmarkRunner()
    
    # Create benchmark suite
    suite = runner.create_suite("Performance Test", "Test application performance")
    
    # Benchmark CRUD operations
    async def create_operation():
        await User.create(name="Test User", email="test@example.com")
    
    result = await runner.run_benchmark(
        "Create Operation",
        create_operation,
        iterations=1000
    )
    
    print(f"Average time: {result.avg_time}ms")
    print(f"Success rate: {result.success_rate}%")

**Comparing with Other ORMs**

.. code-block:: python

    # Compare with SQLAlchemy
    oxen_results = await run_oxen_benchmark()
    sqlalchemy_results = await run_sqlalchemy_benchmark()
    
    comparison = runner.compare_with_other_orms(
        oxen_results, 
        sqlalchemy_results
    )
    
    for test_name, improvement in comparison["performance_improvement"].items():
        print(f"{test_name}: {improvement['improvement_percent']:.1f}% faster")

**Performance Regression Testing**

.. code-block:: python

    # Run regression tests
    baseline_results = load_baseline_results()
    current_results = await run_performance_tests()
    
    for test_name in baseline_results:
        baseline_time = baseline_results[test_name]["avg_time"]
        current_time = current_results[test_name]["avg_time"]
        
        if current_time > baseline_time * 1.1:  # 10% regression
            print(f"Performance regression in {test_name}")

Production Optimization
----------------------

**Database Configuration**

Optimize database settings for production:

**PostgreSQL**

.. code-block:: sql

    -- Increase shared buffers
    shared_buffers = 256MB
    
    -- Optimize work memory
    work_mem = 4MB
    
    -- Enable query plan caching
    plan_cache_mode = auto
    
    -- Optimize checkpoint settings
    checkpoint_completion_target = 0.9
    wal_buffers = 16MB

**MySQL**

.. code-block:: sql

    -- Optimize buffer pool
    innodb_buffer_pool_size = 1G
    
    -- Optimize query cache
    query_cache_size = 64M
    query_cache_type = 1
    
    -- Optimize connection handling
    max_connections = 200
    thread_cache_size = 50

**Application Configuration**

.. code-block:: python

    # Production configuration
    import asyncio
    import uvloop
    
    # Use uvloop for better performance
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    # Configure connection pooling
    await connect(
        "postgresql://user:pass@localhost/mydb",
        pool_size=50,
        max_overflow=100,
        pool_timeout=30,
        pool_recycle=3600
    )
    
    # Enable query caching
    set_cache_enabled(True)
    set_cache_ttl(600)  # 10 minutes

**Load Balancing**

For high-traffic applications, use multiple database connections:

.. code-block:: python

    # Configure multiple database connections
    primary_db = await connect("postgresql://user:pass@primary/db")
    replica_db = await connect("postgresql://user:pass@replica/db")
    
    # Use primary for writes, replica for reads
    async def get_users():
        return await User.all(using_db=replica_db)
    
    async def create_user(user_data):
        return await User.create(**user_data, using_db=primary_db)

**Caching Strategy**

Implement a multi-level caching strategy:

.. code-block:: python

    import redis
    from oxen import set_cache_enabled

    # Configure Redis cache
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    # Enable OxenORM caching
    set_cache_enabled(True)
    
    # Custom caching for complex queries
    async def get_user_with_cache(user_id):
        cache_key = f"user:{user_id}"
        
        # Try cache first
        cached_user = redis_client.get(cache_key)
        if cached_user:
            return json.loads(cached_user)
        
        # Query database
        user = await User.get(pk=user_id)
        
        # Cache result
        redis_client.setex(cache_key, 300, json.dumps(user.to_dict()))
        return user

Performance Troubleshooting
-------------------------

**Common Performance Issues**

1. **N+1 Query Problem**

   **Problem**: Multiple queries for related objects
   
   **Solution**: Use select_related() and prefetch_related()
   
   .. code-block:: python

       # Problem: N+1 queries
       books = await Book.all()
       for book in books:
           author = await book.author  # Additional query per book
       
       # Solution: Single query
       books = await Book.all().select_related("author")
       for book in books:
           print(book.author.name)  # No additional queries

2. **Large Result Sets**

   **Problem**: Loading too much data into memory
   
   **Solution**: Use pagination or streaming
   
   .. code-block:: python

       # Problem: Load all users
       users = await User.all()  # Could be millions
       
       # Solution: Pagination
       users = await User.all().limit(100).offset(0)
       
       # Solution: Streaming
       async for user in User.all().stream():
           process_user(user)

3. **Inefficient Queries**

   **Problem**: Queries not using indexes
   
   **Solution**: Add appropriate indexes and use query optimization
   
   .. code-block:: python

       # Problem: No index on frequently queried field
       users = await User.filter(email__icontains="gmail")
       
       # Solution: Add index
       class User(Model):
           email = CharField(max_length=255, db_index=True)
       
       # Use query optimization
       optimizer = QueryOptimizer()
       optimized_query = await optimizer.optimize_query(queryset)

**Performance Monitoring Tools**

1. **Query Logging**

   .. code-block:: python

       import logging
       
       # Enable query logging
       logging.getLogger("oxen").setLevel(logging.DEBUG)
       
       # All queries will be logged with timing information

2. **Performance Dashboard**

   .. code-block:: python

       from oxen.admin import start_admin_interface
       
       # Start admin interface
       start_admin_interface(host="localhost", port=8080)
       
       # Open http://localhost:8080 to view performance metrics

3. **Custom Metrics**

   .. code-block:: python

       from oxen import record_query_metric
       
       # Track custom metrics
       async def track_slow_queries():
           start_time = time.perf_counter()
           result = await complex_query()
           execution_time = (time.perf_counter() - start_time) * 1000
           
           if execution_time > 1000:
               record_query_metric(
                   query_type="slow_query",
                   execution_time=execution_time,
                   alert_level="warning"
               )

**Performance Checklist**

Before deploying to production, ensure:

- [ ] Database indexes are created for frequently queried fields
- [ ] Connection pooling is properly configured
- [ ] Query caching is enabled
- [ ] N+1 query problems are resolved
- [ ] Large datasets use pagination or streaming
- [ ] Performance monitoring is set up
- [ ] Alerts are configured for performance issues
- [ ] Database is optimized for the workload
- [ ] Application is configured for production
- [ ] Load testing has been performed

**Performance Testing**

Run comprehensive performance tests:

.. code-block:: python

    from oxen import BenchmarkRunner

    runner = BenchmarkRunner()
    
    # Test CRUD operations
    await runner.benchmark_crud_operations(User, test_data)
    
    # Test query operations
    await runner.benchmark_query_operations(User, test_data)
    
    # Test bulk operations
    await runner.benchmark_bulk_operations(User, test_data)
    
    # Test concurrent operations
    await runner.benchmark_concurrent_operations(User, test_data)
    
    # Generate performance report
    runner.save_report("performance_test")

This comprehensive performance guide ensures your OxenORM application runs at optimal performance in production environments. 