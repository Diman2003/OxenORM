#!/usr/bin/env python3
"""
Test for Query Optimization System

This test demonstrates the query optimization features including:
- Query plan analysis
- Performance monitoring
- Optimization suggestions
- Index recommendations
"""

import asyncio
import sys
import uuid
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField, BooleanField, DateTimeField
from oxen.fields.relational import ForeignKeyField
from oxen.migrations import MigrationEngine
from oxen.query_optimizer import QueryOptimizer, QueryAnalyzer, IndexAnalyzer
from oxen.engine import UnifiedEngine


# Test models for optimization testing
class User(Model):
    """User model for testing query optimization."""
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    age = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"users_{uuid.uuid4().hex[:8]}"


class Product(Model):
    """Product model for testing query optimization."""
    name = CharField(max_length=200)
    price = IntegerField(default=0)
    category = CharField(max_length=100)
    description = CharField(max_length=500)
    is_available = BooleanField(default=True)
    user = ForeignKeyField(User, related_name="products")
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"products_{uuid.uuid4().hex[:8]}"


class Order(Model):
    """Order model for testing query optimization."""
    order_number = CharField(max_length=50, unique=True)
    total_amount = IntegerField(default=0)
    status = CharField(max_length=50, default="pending")
    user = ForeignKeyField(User, related_name="orders")
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"orders_{uuid.uuid4().hex[:8]}"


async def test_query_optimization():
    """Test the query optimization system."""
    print("🚀 Query Optimization Test")
    print("=" * 40)
    
    # Connect to database
    db_id = uuid.uuid4().hex[:8]
    db_name = f"test_query_optimization_{db_id}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Set database for all models
    set_database_for_models(engine)
    
    # Generate and run migrations
    print("🔄 Generating migrations...")
    migration_engine = MigrationEngine(engine, migrations_dir="../migrations")
    
    models = [User, Product, Order]
    migration = await migration_engine.generate_migration_from_models(
        models, f"test_query_optimization_{db_id}", "test_runner"
    )
    
    if migration:
        print("✅ Migration generated successfully")
        
        print("🔄 Running migrations...")
        result = await migration_engine.run_migrations()
        print(f"Migration result: {result}")
        
        if result.get('success') or result.get('migrations_run', 0) > 0:
            print("✅ Migration executed successfully")
        else:
            print("❌ Migration failed")
            return
    else:
        print("❌ Failed to generate migration")
        return
    
    print("✅ Database setup complete")
    
    # Create test data
    print("\n🔄 Creating test data...")
    
    # Create users
    users = []
    for i in range(100):
        user = await User.create(
            name=f"User {i}",
            email=f"user{i}@example.com",
            age=20 + (i % 50),
            is_active=i % 10 != 0  # 90% active users
        )
        users.append(user)
    
    # Create products
    products = []
    categories = ["Electronics", "Books", "Clothing", "Food", "Sports"]
    for i in range(500):
        product = await Product.create(
            name=f"Product {i}",
            price=1000 + (i * 100),  # $10 to $510
            category=categories[i % len(categories)],
            description=f"Description for product {i}",
            is_available=i % 20 != 0,  # 95% available
            user=users[i % len(users)]
        )
        products.append(product)
    
    # Create orders
    orders = []
    statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    for i in range(200):
        order = await Order.create(
            order_number=f"ORD-{i:06d}",
            total_amount=5000 + (i * 50),  # $50 to $1050
            status=statuses[i % len(statuses)],
            user=users[i % len(users)]
        )
        orders.append(order)
    
    print("✅ Test data created")
    
    # Test 1: Query Analysis
    print("\n🔄 Test 1: Query Analysis")
    print("-" * 50)
    
    try:
        analyzer = QueryAnalyzer()
        
        # Test different query types
        test_queries = [
            ("SELECT * FROM users", 0.1, 100),
            ("SELECT name, email FROM users WHERE age > 30", 0.05, 50),
            ("SELECT * FROM products WHERE category = 'Electronics' AND price > 2000", 0.2, 80),
            ("SELECT u.name, COUNT(p.id) FROM users u JOIN products p ON u.id = p.user_id GROUP BY u.id", 0.5, 100),
            ("SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC", 0.15, 40),
        ]
        
        for sql, execution_time, rows_affected in test_queries:
            plan = analyzer.analyze_query(sql, execution_time, rows_affected)
            print(f"   Query: {sql[:50]}...")
            print(f"   Performance Score: {plan.performance_score:.1f}/100")
            print(f"   Suggestions: {len(plan.optimization_suggestions)}")
            for suggestion in plan.optimization_suggestions[:2]:  # Show first 2
                print(f"     - {suggestion}")
            print()
        
        print("✅ Query analysis test completed")
        
    except Exception as e:
        print(f"   ❌ Query analysis test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Performance Monitoring
    print("\n🔄 Test 2: Performance Monitoring")
    print("-" * 50)
    
    try:
        optimizer = QueryOptimizer()
        
        # Simulate some queries with different performance characteristics
        test_scenarios = [
            ("SELECT * FROM users", 0.05, 100, "Fast query"),
            ("SELECT * FROM products WHERE category = 'Electronics'", 0.1, 100, "Medium query"),
            ("SELECT * FROM orders WHERE status = 'pending'", 0.15, 40, "Slower query"),
            ("SELECT u.name, p.name FROM users u JOIN products p ON u.id = p.user_id", 0.3, 500, "Complex join"),
            ("SELECT * FROM users WHERE email LIKE '%@example.com'", 0.8, 100, "Slow LIKE query"),
        ]
        
        for sql, execution_time, rows_affected, description in test_scenarios:
            plan = optimizer.optimize_query(sql, execution_time, rows_affected)
            print(f"   {description}:")
            print(f"     Execution Time: {execution_time:.3f}s")
            print(f"     Performance Score: {plan.performance_score:.1f}/100")
            print(f"     Suggestions: {len(plan.optimization_suggestions)}")
            print()
        
        # Get performance stats
        stats = optimizer.get_performance_stats()
        print(f"   Performance Statistics:")
        print(f"     Total Queries: {stats.get('total_queries', 0)}")
        print(f"     Avg Execution Time: {stats.get('avg_execution_time', 0):.3f}s")
        print(f"     Avg Performance Score: {stats.get('avg_performance_score', 0):.1f}/100")
        print(f"     Slow Queries: {stats.get('slow_queries_count', 0)}")
        print(f"     Critical Queries: {stats.get('critical_queries_count', 0)}")
        
        print("✅ Performance monitoring test completed")
        
    except Exception as e:
        print(f"   ❌ Performance monitoring test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Index Recommendations
    print("\n🔄 Test 3: Index Recommendations")
    print("-" * 50)
    
    try:
        index_analyzer = IndexAnalyzer()
        
        # Simulate schema information
        schema_info = {
            'users': {
                'columns': [
                    {'name': 'id', 'is_primary_key': True},
                    {'name': 'email', 'is_unique': True, 'used_in_where': True},
                    {'name': 'age', 'used_in_where': True, 'used_in_order_by': True},
                    {'name': 'is_active', 'used_in_where': True},
                ]
            },
            'products': {
                'columns': [
                    {'name': 'id', 'is_primary_key': True},
                    {'name': 'user_id', 'is_foreign_key': True, 'used_in_where': True},
                    {'name': 'category', 'used_in_where': True},
                    {'name': 'price', 'used_in_where': True, 'used_in_order_by': True},
                    {'name': 'is_available', 'used_in_where': True},
                ]
            },
            'orders': {
                'columns': [
                    {'name': 'id', 'is_primary_key': True},
                    {'name': 'user_id', 'is_foreign_key': True, 'used_in_where': True},
                    {'name': 'status', 'used_in_where': True},
                    {'name': 'created_at', 'used_in_order_by': True},
                ]
            }
        }
        
        recommendations = index_analyzer.analyze_schema(schema_info)
        
        print(f"   Generated {len(recommendations)} index recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):  # Show first 5
            print(f"     {i}. {rec.table_name}.{rec.column_name} ({rec.index_type})")
            print(f"        Reason: {rec.reason}")
            print(f"        Priority: {rec.priority.value}")
            print(f"        Estimated Improvement: {rec.estimated_improvement:.1%}")
            print()
        
        print("✅ Index recommendations test completed")
        
    except Exception as e:
        print(f"   ❌ Index recommendations test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Real Query Performance
    print("\n🔄 Test 4: Real Query Performance")
    print("-" * 50)
    
    try:
        # Execute some real queries and monitor performance
        queries = [
            "SELECT * FROM users LIMIT 10",
            "SELECT * FROM products WHERE category = 'Electronics'",
            "SELECT u.name, COUNT(p.id) FROM users u JOIN products p ON u.id = p.user_id GROUP BY u.id",
            "SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC",
        ]
        
        for i, sql in enumerate(queries, 1):
            print(f"   Query {i}: {sql[:50]}...")
            
            start_time = time.time()
            result = await engine.execute_query(sql)
            execution_time = time.time() - start_time
            
            if result.get('success'):
                rows_affected = len(result.get('data', []))
                optimization = result.get('optimization', {})
                
                print(f"     Execution Time: {execution_time:.3f}s")
                print(f"     Rows Affected: {rows_affected}")
                print(f"     Performance Score: {optimization.get('performance_score', 0):.1f}/100")
                
                suggestions = optimization.get('suggestions', [])
                if suggestions:
                    print(f"     Suggestions: {len(suggestions)}")
                    for suggestion in suggestions[:2]:
                        print(f"       - {suggestion}")
                print()
            else:
                print(f"     Error: {result.get('error')}")
                print()
        
        print("✅ Real query performance test completed")
        
    except Exception as e:
        print(f"   ❌ Real query performance test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Performance Report Export
    print("\n🔄 Test 5: Performance Report Export")
    print("-" * 50)
    
    try:
        # Export performance report
        report_filename = f"performance_report_{db_id}.json"
        from oxen.query_optimizer import export_performance_report
        export_performance_report(report_filename)
        
        print(f"   ✅ Performance report exported to: {report_filename}")
        
        # Show report summary
        from oxen.query_optimizer import get_performance_stats
        stats = get_performance_stats()
        
        print(f"   Report Summary:")
        print(f"     Total Queries Analyzed: {stats.get('total_queries', 0)}")
        print(f"     Average Execution Time: {stats.get('avg_execution_time', 0):.3f}s")
        print(f"     Average Performance Score: {stats.get('avg_performance_score', 0):.1f}/100")
        print(f"     Optimization Suggestions: {stats.get('optimization_suggestions_count', 0)}")
        
        print("✅ Performance report export test completed")
        
    except Exception as e:
        print(f"   ❌ Performance report export test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")
    print("✅ Query optimization test completed!")


if __name__ == "__main__":
    asyncio.run(test_query_optimization()) 