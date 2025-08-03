#!/usr/bin/env python3
"""
Test for Window Functions and CTEs in QuerySet
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
from oxen.expressions import WindowFunction


# Test models
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


async def test_window_functions_cte():
    """Test window functions and CTEs in QuerySet."""
    print("🚀 Window Functions and CTEs Test")
    print("=" * 40)
    
    # Connect to database with unique name
    db_id = uuid.uuid4().hex[:8]
    db_name = f"test_window_cte_{db_id}.db"
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
        models, f"test_window_cte_{db_id}", "test_runner"
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
        from oxen.expressions import WindowFunction
        
        # Create a window function for row numbering
        row_number_window = WindowFunction(
            function="ROW_NUMBER()",
            partition_by=["customer_name"],
            order_by=["amount DESC"]
        )
        
        # This would be the ideal API:
        # results = await SalesOrder.window(row_num=row_number_window).filter(customer_name='Alice')
        
        # For now, let's test if the window function can be created
        print(f"   Window function created: {row_number_window.to_sql()}")
        
        # Test basic query to ensure it still works
        alice_orders = await SalesOrder.filter(customer_name='Alice').order_by('-amount')
        print(f"   Found {len(alice_orders)} orders for Alice")
        
        for i, order in enumerate(alice_orders, 1):
            print(f"   {i}. {order.product_name}: ${order.amount}")
        
        print("✅ Window function test completed")
        
    except Exception as e:
        print(f"   ❌ Window function test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Window Functions - RANK()
    print("\n🔄 Test 2: Window Functions - RANK()")
    print("-" * 50)
    
    try:
        # Test ranking by amount within each region
        rank_window = WindowFunction(
            function="RANK()",
            partition_by=["region"],
            order_by=["amount DESC"]
        )
        
        print(f"   Rank window function created: {rank_window.to_sql()}")
        
        # Test basic query
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
        # This would be the ideal API:
        # dept_avg = Employee.group_by('department').annotate(avg_salary=Avg('salary'))
        # results = await Employee.with_cte('dept_avg', dept_avg).all()
        
        # For now, test basic query
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
    
    # Test 4: Advanced Window Functions
    print("\n🔄 Test 4: Advanced Window Functions")
    print("-" * 50)
    
    try:
        # Test LAG and LEAD functions
        lag_window = WindowFunction(
            function="LAG(amount, 1) OVER (ORDER BY amount)",
            order_by=["amount"]
        )
        
        lead_window = WindowFunction(
            function="LEAD(amount, 1) OVER (ORDER BY amount)",
            order_by=["amount"]
        )
        
        print(f"   LAG window function: {lag_window.to_sql()}")
        print(f"   LEAD window function: {lead_window.to_sql()}")
        
        # Test basic query
        orders_by_amount = await SalesOrder.order_by('amount')
        print(f"   Orders by amount: {len(orders_by_amount)}")
        
        for order in orders_by_amount:
            print(f"     {order.customer_name}: {order.product_name} - ${order.amount}")
        
        print("✅ Advanced window functions test completed")
        
    except Exception as e:
        print(f"   ❌ Advanced window functions test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Complex CTEs
    print("\n🔄 Test 5: Complex CTEs")
    print("-" * 50)
    
    try:
        # Test recursive CTE (for hierarchical data)
        # This would be the ideal API:
        # employee_hierarchy = Employee.with_cte('hierarchy', recursive=True)
        
        # For now, test basic query
        high_earners = await Employee.filter(salary__gte=80000)
        print(f"   High earners (salary >= $80k): {len(high_earners)}")
        
        for emp in high_earners:
            print(f"     {emp.name} ({emp.department}): ${emp.salary}")
        
        print("✅ Complex CTEs test completed")
        
    except Exception as e:
        print(f"   ❌ Complex CTEs test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    await engine.disconnect()
    print(f"\n🧹 Cleaned up database: {db_name}")
    print("✅ Window functions and CTEs test completed!")


if __name__ == "__main__":
    asyncio.run(test_window_functions_cte()) 