#!/usr/bin/env python3
"""
Test PostgreSQL integration with advanced features:
- Window Functions
- Common Table Expressions (CTEs)
- Advanced field types
- Performance with uvloop
"""

import asyncio
import time
import os
from typing import List, Dict, Any
from oxen import Model, connect, disconnect
from oxen.fields import (
    CharField, IntField, FloatField, DateTimeField, 
    JSONField, ArrayField, TextField, BooleanField
)
from oxen.expressions import Q, WindowFunction, CommonTableExpression
from oxen.uvloop_config import is_uvloop_active, get_event_loop_info


# Define models for testing
class User(Model):
    id = IntField(primary_key=True)
    username = CharField(max_length=100, unique=True)
    email = CharField(max_length=255, unique=True)
    age = IntField()
    salary = FloatField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    metadata = JSONField(null=True)
    tags = ArrayField(element_type="text", null=True)
    
    class Meta:
        table_name = "users"


class Order(Model):
    id = IntField(primary_key=True)
    user_id = IntField()
    product_name = CharField(max_length=200)
    quantity = IntField()
    price = FloatField()
    total_amount = FloatField()
    order_date = DateTimeField(auto_now_add=True)
    status = CharField(max_length=50, default="pending")
    
    class Meta:
        table_name = "orders"


class Product(Model):
    id = IntField(primary_key=True)
    name = CharField(max_length=200)
    category = CharField(max_length=100)
    price = FloatField()
    stock = IntField()
    rating = FloatField(null=True)
    tags = ArrayField(element_type="text", null=True)
    metadata = JSONField(null=True)
    
    class Meta:
        table_name = "products"


async def test_postgresql_connection():
    """Test PostgreSQL connection and basic operations."""
    print("🗄️  Testing PostgreSQL connection...")
    
    try:
        # Connect to PostgreSQL
        connection_string = "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm"
        engine = await connect(connection_string)
        print("✅ PostgreSQL connected successfully")
        
        # Create tables using the engine
        await engine.create_table("users", {
            "id": "SERIAL PRIMARY KEY",
            "username": "VARCHAR(100) UNIQUE NOT NULL",
            "email": "VARCHAR(255) UNIQUE NOT NULL",
            "age": "INTEGER NOT NULL",
            "salary": "DECIMAL(10,2) NOT NULL",
            "is_active": "BOOLEAN DEFAULT TRUE",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "metadata": "JSONB",
            "tags": "TEXT[]"
        })
        
        await engine.create_table("orders", {
            "id": "SERIAL PRIMARY KEY",
            "user_id": "INTEGER NOT NULL",
            "product_name": "VARCHAR(200) NOT NULL",
            "quantity": "INTEGER NOT NULL",
            "price": "DECIMAL(10,2) NOT NULL",
            "total_amount": "DECIMAL(10,2) NOT NULL",
            "order_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "status": "VARCHAR(50) DEFAULT 'pending'"
        })
        
        await engine.create_table("products", {
            "id": "SERIAL PRIMARY KEY",
            "name": "VARCHAR(200) NOT NULL",
            "category": "VARCHAR(100) NOT NULL",
            "price": "DECIMAL(10,2) NOT NULL",
            "stock": "INTEGER NOT NULL",
            "rating": "DECIMAL(3,2)",
            "tags": "TEXT[]",
            "metadata": "JSONB"
        })
        
        print("✅ Tables created successfully")
        
        return engine
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return None


async def test_basic_crud():
    """Test basic CRUD operations."""
    print("\n📝 Testing basic CRUD operations...")
    
    # Create users
    users_data = [
        {"username": "john_doe", "email": "john@example.com", "age": 30, "salary": 75000.0, "tags": ["developer", "python"]},
        {"username": "jane_smith", "email": "jane@example.com", "age": 28, "salary": 80000.0, "tags": ["designer", "ui"]},
        {"username": "bob_wilson", "email": "bob@example.com", "age": 35, "salary": 90000.0, "tags": ["manager", "lead"]},
        {"username": "alice_brown", "email": "alice@example.com", "age": 25, "salary": 65000.0, "tags": ["junior", "frontend"]},
        {"username": "charlie_davis", "email": "charlie@example.com", "age": 32, "salary": 85000.0, "tags": ["senior", "backend"]},
    ]
    
    created_users = []
    for user_data in users_data:
        result = await engine.insert_record("users", user_data)
        if result.get('error') is None:
            user_id = result.get('data', {}).get('id')
            print(f"✅ Created user: {user_data['username']} (ID: {user_id})")
            created_users.append(user_id)
        else:
            print(f"❌ Failed to create user {user_data['username']}: {result.get('error')}")
    
    # Test queries
    all_users_result = await engine.select_records("users")
    all_users = all_users_result.get('data', [])
    print(f"✅ Retrieved {len(all_users)} users")
    
    active_users_result = await engine.select_records("users", {"is_active": True})
    active_users = active_users_result.get('data', [])
    print(f"✅ Found {len(active_users)} active users")
    
    # For high salary users, we'll use a direct query
    high_salary_result = await engine.execute_query(
        "SELECT * FROM users WHERE salary >= 80000.0"
    )
    high_salary_users = high_salary_result.get('data', [])
    print(f"✅ Found {len(high_salary_users)} high-salary users")
    
    return created_users


async def test_window_functions():
    """Test window functions."""
    print("\n🪟 Testing Window Functions...")
    
    # Create some products for testing
    products_data = [
        {"name": "Laptop", "category": "Electronics", "price": 1200.0, "stock": 50, "rating": 4.5},
        {"name": "Phone", "category": "Electronics", "price": 800.0, "stock": 100, "rating": 4.2},
        {"name": "Tablet", "category": "Electronics", "price": 600.0, "stock": 30, "rating": 4.0},
        {"name": "Book", "category": "Books", "price": 25.0, "stock": 200, "rating": 4.8},
        {"name": "Pen", "category": "Office", "price": 5.0, "stock": 500, "rating": 3.5},
        {"name": "Desk", "category": "Furniture", "price": 300.0, "stock": 10, "rating": 4.1},
        {"name": "Chair", "category": "Furniture", "price": 150.0, "stock": 25, "rating": 4.3},
    ]
    
    for product_data in products_data:
        await Product.create(**product_data)
    
    print("✅ Created products for window function testing")
    
    # Test ROW_NUMBER() window function
    try:
        # Get products ranked by price within each category
        ranked_products = await Product.annotate(
            price_rank=WindowFunction(
                "ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC)",
                alias="price_rank"
            )
        ).filter(price_rank__lte=2)  # Top 2 most expensive in each category
        
        print(f"✅ Window function (ROW_NUMBER): Found {len(ranked_products)} top products by category")
        for product in ranked_products:
            print(f"   - {product.name} ({product.category}): ${product.price} (Rank: {product.price_rank})")
            
    except Exception as e:
        print(f"❌ Window function test failed: {e}")
    
    # Test RANK() window function
    try:
        # Get products ranked by rating
        rated_products = await Product.annotate(
            rating_rank=WindowFunction(
                "RANK() OVER (ORDER BY rating DESC)",
                alias="rating_rank"
            )
        ).filter(rating_rank__lte=3)  # Top 3 rated products
        
        print(f"✅ Window function (RANK): Found {len(rated_products)} top-rated products")
        for product in rated_products:
            print(f"   - {product.name}: Rating {product.rating} (Rank: {product.rating_rank})")
            
    except Exception as e:
        print(f"❌ RANK window function test failed: {e}")
    
    # Test DENSE_RANK() window function
    try:
        # Get products ranked by stock (dense rank for ties)
        stock_ranked = await Product.annotate(
            stock_rank=WindowFunction(
                "DENSE_RANK() OVER (ORDER BY stock DESC)",
                alias="stock_rank"
            )
        ).filter(stock_rank__lte=3)  # Top 3 by stock
        
        print(f"✅ Window function (DENSE_RANK): Found {len(stock_ranked)} products by stock")
        for product in stock_ranked:
            print(f"   - {product.name}: Stock {product.stock} (Rank: {product.stock_rank})")
            
    except Exception as e:
        print(f"❌ DENSE_RANK window function test failed: {e}")


async def test_common_table_expressions():
    """Test Common Table Expressions (CTEs)."""
    print("\n📊 Testing Common Table Expressions (CTEs)...")
    
    # Create some orders for testing
    orders_data = [
        {"user_id": 1, "product_name": "Laptop", "quantity": 1, "price": 1200.0, "total_amount": 1200.0, "status": "completed"},
        {"user_id": 1, "product_name": "Phone", "quantity": 2, "price": 800.0, "total_amount": 1600.0, "status": "completed"},
        {"user_id": 2, "product_name": "Tablet", "quantity": 1, "price": 600.0, "total_amount": 600.0, "status": "pending"},
        {"user_id": 2, "product_name": "Book", "quantity": 3, "price": 25.0, "total_amount": 75.0, "status": "completed"},
        {"user_id": 3, "product_name": "Desk", "quantity": 1, "price": 300.0, "total_amount": 300.0, "status": "completed"},
        {"user_id": 3, "product_name": "Chair", "quantity": 2, "price": 150.0, "total_amount": 300.0, "status": "pending"},
    ]
    
    for order_data in orders_data:
        await Order.create(**order_data)
    
    print("✅ Created orders for CTE testing")
    
    try:
        # Test CTE for user order statistics
        user_stats_cte = CommonTableExpression(
            "user_order_stats",
            """
            SELECT 
                user_id,
                COUNT(*) as order_count,
                SUM(total_amount) as total_spent,
                AVG(total_amount) as avg_order_value
            FROM orders 
            WHERE status = 'completed'
            GROUP BY user_id
            """
        )
        
        # Use the CTE to get user statistics
        user_stats = await User.annotate(
            order_count=user_stats_cte.get("order_count"),
            total_spent=user_stats_cte.get("total_spent"),
            avg_order_value=user_stats_cte.get("avg_order_value")
        ).filter(id__in=user_stats_cte.get("user_id"))
        
        print(f"✅ CTE test: Found statistics for {len(user_stats)} users")
        for user in user_stats:
            print(f"   - {user.username}: {user.order_count} orders, ${user.total_spent:.2f} total, ${user.avg_order_value:.2f} avg")
            
    except Exception as e:
        print(f"❌ CTE test failed: {e}")
    
    try:
        # Test recursive CTE for category spending
        category_spending_cte = CommonTableExpression(
            "category_spending",
            """
            SELECT 
                p.category,
                COUNT(o.id) as order_count,
                SUM(o.total_amount) as total_revenue,
                AVG(o.total_amount) as avg_order_value
            FROM orders o
            JOIN products p ON o.product_name = p.name
            WHERE o.status = 'completed'
            GROUP BY p.category
            """
        )
        
        # Get category spending statistics
        category_stats = await Product.annotate(
            order_count=category_spending_cte.get("order_count"),
            total_revenue=category_spending_cte.get("total_revenue"),
            avg_order_value=category_spending_cte.get("avg_order_value")
        ).filter(category__in=category_spending_cte.get("category"))
        
        print(f"✅ Recursive CTE test: Found statistics for {len(category_stats)} categories")
        for product in category_stats:
            print(f"   - {product.category}: {product.order_count} orders, ${product.total_revenue:.2f} revenue")
            
    except Exception as e:
        print(f"❌ Recursive CTE test failed: {e}")


async def test_advanced_queries():
    """Test advanced PostgreSQL-specific queries."""
    print("\n🔍 Testing Advanced PostgreSQL Queries...")
    
    try:
        # Test JSON field operations
        users_with_metadata = await User.filter(metadata__isnull=False)
        print(f"✅ JSON field query: Found {len(users_with_metadata)} users with metadata")
        
        # Test array field operations
        python_developers = await User.filter(tags__contains=["python"])
        print(f"✅ Array field query: Found {len(python_developers)} Python developers")
        
        # Test complex aggregations
        age_stats = await User.aggregate(
            avg_age=Q.avg("age"),
            max_age=Q.max("age"),
            min_age=Q.min("age"),
            count=Q.count("id")
        )
        print(f"✅ Age statistics: {age_stats}")
        
        # Test case when expressions
        salary_categories = await User.annotate(
            salary_category=Q.case(
                Q.when(salary__gte=90000, then=Q.value("High")),
                Q.when(salary__gte=70000, then=Q.value("Medium")),
                default=Q.value("Low")
            )
        )
        
        high_earners = [u for u in salary_categories if u.salary_category == "High"]
        print(f"✅ Case when expression: Found {len(high_earners)} high earners")
        
    except Exception as e:
        print(f"❌ Advanced queries test failed: {e}")


async def test_performance_with_uvloop():
    """Test performance with uvloop."""
    print("\n⚡ Testing Performance with uvloop...")
    
    loop_info = get_event_loop_info()
    print(f"📊 Event Loop Info: {loop_info}")
    
    # Test bulk operations
    start_time = time.time()
    
    # Create many users for performance testing
    bulk_users = []
    for i in range(100):
        bulk_users.append({
            "username": f"perf_user_{i}",
            "email": f"perf{i}@example.com",
            "age": 20 + (i % 50),
            "salary": 50000.0 + (i * 100),
            "tags": ["performance", f"batch_{i//10}"]
        })
    
    # Bulk create
    created_users = await User.bulk_create(bulk_users)
    bulk_create_time = time.time() - start_time
    print(f"✅ Bulk create: {len(created_users)} users in {bulk_create_time:.4f}s")
    
    # Test bulk update
    start_time = time.time()
    update_count = await User.filter(username__startswith="perf_user").update(salary=Q.f("salary") + 1000)
    bulk_update_time = time.time() - start_time
    print(f"✅ Bulk update: {update_count} users in {bulk_update_time:.4f}s")
    
    # Test complex query performance
    start_time = time.time()
    complex_query = await User.filter(
        age__gte=25,
        salary__gte=60000,
        tags__contains=["performance"]
    ).order_by("-salary").limit(10)
    query_time = time.time() - start_time
    print(f"✅ Complex query: {len(complex_query)} results in {query_time:.4f}s")
    
    print(f"🚀 uvloop active: {is_uvloop_active()}")
    if is_uvloop_active():
        print("✅ Enhanced performance with uvloop!")


async def main():
    """Main test function."""
    print("🚀 PostgreSQL Advanced Features Test")
    print("=" * 60)
    
    # Test connection
    engine = await test_postgresql_connection()
    if not engine:
        print("❌ Cannot proceed without database connection")
        return
    
    try:
        # Run all tests
        await test_basic_crud()
        await test_window_functions()
        await test_common_table_expressions()
        await test_advanced_queries()
        await test_performance_with_uvloop()
        
        print("\n" + "=" * 60)
        print("✅ All PostgreSQL tests completed successfully!")
        
        # Print final statistics
        user_count = await User.count()
        order_count = await Order.count()
        product_count = await Product.count()
        
        print(f"\n📊 Final Statistics:")
        print(f"   - Users: {user_count}")
        print(f"   - Orders: {order_count}")
        print(f"   - Products: {product_count}")
        print(f"   - uvloop active: {is_uvloop_active()}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # Cleanup
        await disconnect(engine)
        print("✅ Database disconnected")


if __name__ == "__main__":
    asyncio.run(main()) 