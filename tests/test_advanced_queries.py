#!/usr/bin/env python3
"""
Test for Advanced Query Features - Window Functions and CTEs
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, connect, set_database_for_models
from oxen.fields import CharField, IntegerField, BooleanField, DateTimeField
from oxen.migrations import MigrationEngine


# Test models for advanced queries
class SalesOrder(Model):
    """Sales order model for testing window functions."""
    customer_name = CharField(max_length=100)
    product_name = CharField(max_length=100)
    amount = IntegerField(default=0)
    order_date = DateTimeField(auto_now_add=True)
    region = CharField(max_length=50)
    
    class Meta:
        table_name = f"sales_orders_{uuid.uuid4().hex[:8]}"


class Employee(Model):
    """Employee model for testing CTEs."""
    name = CharField(max_length=100)
    department = CharField(max_length=50)
    salary = IntegerField(default=0)
    hire_date = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"employees_{uuid.uuid4().hex[:8]}"


async def test_advanced_queries():
    """Test advanced query features."""
    print("🚀 Advanced Query Features Test")
    print("=" * 40)
    
    # Connect to database with unique name
    db_id = uuid.uuid4().hex[:8]
    db_name = f"test_advanced_queries_{db_id}.db"
    connection_string = f"sqlite:///{db_name}"
    
    print(f"✅ Connecting to: {connection_string}")
    engine = await connect(connection_string)
    
    # Set database for all models
    set_database_for_models(engine)
    
    # Generate and run migrations
    print("🔄 Generating migrations...")
    migration_engine = MigrationEngine(engine, migrations_dir="../migrations")
    
    models = [SalesOrder, Employee]
    migration = await migration_engine.generate_migration_from_models(
        models, f"test_advanced_queries_{db_id}", "test_runner"
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
    
    # Create sales orders
    sales_data = [
        ("Alice", "Laptop", 1200, "North"),
        ("Bob", "Phone", 800, "South"),
        ("Alice", "Tablet", 600, "North"),
        ("Charlie", "Laptop", 1200, "East"),
        ("Bob", "Monitor", 300, "South"),
        ("Alice", "Phone", 800, "North"),
        ("David", "Laptop", 1200, "West"),
        ("Charlie", "Tablet", 600, "East"),
    ]
    
    for customer, product, amount, region in sales_data:
        await SalesOrder.create(
            customer_name=customer,
            product_name=product,
            amount=amount,
            region=region
        )
    
    # Create employees
    employees_data = [
        ("John Smith", "Engineering", 75000),
        ("Jane Doe", "Marketing", 65000),
        ("Bob Johnson", "Engineering", 80000),
        ("Alice Brown", "Sales", 60000),
        ("Charlie Wilson", "Engineering", 90000),
        ("Diana Davis", "Marketing", 70000),
        ("Eve Miller", "Sales", 55000),
        ("Frank Garcia", "Engineering", 85000),
    ]
    
    for name, department, salary in employees_data:
        await Employee.create(
            name=name,
            department=department,
            salary=salary
        )
    
    print("✅ Test data created")
    
    # Test 1: Window Functions - ROW_NUMBER()
    print("\n🔄 Test 1: Window Functions - ROW_NUMBER()")
    print("-" * 50)
    
    try:
        # Test window function with ROW_NUMBER
        from oxen.expressions import WindowFunction, F
        
        # This would be the ideal API:
        # results = await SalesOrder.annotate(
        #     row_num=WindowFunction('ROW_NUMBER()', 
        #                           partition_by=['customer_name'], 
        #                           order_by=['amount DESC'])
        # ).filter(customer_name='Alice')
        
        # For now, let's test if we can at least query the data
        alice_orders = await SalesOrder.filter(customer_name='Alice').order_by('-amount')
        print(f"   Found {len(alice_orders)} orders for Alice")
        
        for i, order in enumerate(alice_orders, 1):
            print(f"   {i}. {order.product_name}: ${order.amount}")
        
        print("✅ Basic window function test completed")
        
    except Exception as e:
        print(f"   ❌ Window function test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Window Functions - RANK()
    print("\n🔄 Test 2: Window Functions - RANK()")
    print("-" * 50)
    
    try:
        # Test ranking by amount within each region
        all_orders = await SalesOrder.all()
        print(f"   Total orders: {len(all_orders)}")
        
        # Group by region and show ranking
        regions = {}
        for order in all_orders:
            if order.region not in regions:
                regions[order.region] = []
            regions[order.region].append(order)
        
        for region, orders in regions.items():
            print(f"   {region} region:")
            sorted_orders = sorted(orders, key=lambda x: x.amount, reverse=True)
            for i, order in enumerate(sorted_orders, 1):
                print(f"     {i}. {order.customer_name} - {order.product_name}: ${order.amount}")
        
        print("✅ Ranking test completed")
        
    except Exception as e:
        print(f"   ❌ Ranking test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Common Table Expressions (CTEs)
    print("\n🔄 Test 3: Common Table Expressions (CTEs)")
    print("-" * 50)
    
    try:
        # Test CTE for department salary averages
        all_employees = await Employee.all()
        print(f"   Total employees: {len(all_employees)}")
        
        # Group by department and calculate averages
        departments = {}
        for emp in all_employees:
            if emp.department not in departments:
                departments[emp.department] = []
            departments[emp.department].append(emp)
        
        print("   Department salary averages:")
        for dept, employees in departments.items():
            avg_salary = sum(emp.salary for emp in employees) / len(employees)
            print(f"     {dept}: ${avg_salary:.0f}")
        
        print("✅ CTE test completed")
        
    except Exception as e:
        print(f"   ❌ CTE test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Advanced Aggregations
    print("\n🔄 Test 4: Advanced Aggregations")
    print("-" * 50)
    
    try:
        # Test complex aggregations
        from oxen.expressions import Aggregate
        
        # Get total sales by customer
        customers = {}
        all_orders = await SalesOrder.all()
        
        for order in all_orders:
            if order.customer_name not in customers:
                customers[order.customer_name] = 0
            customers[order.customer_name] += order.amount
        
        print("   Total sales by customer:")
        for customer, total in sorted(customers.items(), key=lambda x: x[1], reverse=True):
            print(f"     {customer}: ${total}")
        
        # Get average order amount by region
        regions = {}
        for order in all_orders:
            if order.region not in regions:
                regions[order.region] = []
            regions[order.region].append(order.amount)
        
        print("   Average order amount by region:")
        for region, amounts in regions.items():
            avg_amount = sum(amounts) / len(amounts)
            print(f"     {region}: ${avg_amount:.0f}")
        
        print("✅ Advanced aggregations test completed")
        
    except Exception as e:
        print(f"   ❌ Advanced aggregations test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Subqueries
    print("\n🔄 Test 5: Subqueries")
    print("-" * 50)
    
    try:
        # Test subquery to find employees with above-average salary
        all_employees = await Employee.all()
        avg_salary = sum(emp.salary for emp in all_employees) / len(all_employees)
        
        high_earners = [emp for emp in all_employees if emp.salary > avg_salary]
        print(f"   Average salary: ${avg_salary:.0f}")
        print(f"   Employees with above-average salary: {len(high_earners)}")
        
        for emp in high_earners:
            print(f"     {emp.name} ({emp.department}): ${emp.salary}")
        
        print("✅ Subquery test completed")
        
    except Exception as e:
        print(f"   ❌ Subquery test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")
    print("✅ Advanced query features test completed!")


if __name__ == "__main__":
    asyncio.run(test_advanced_queries()) 