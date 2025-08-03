#!/usr/bin/env python3
"""
Basic SQLite test to verify core functionality
"""

import asyncio
import time
from oxen import connect, disconnect
from oxen.uvloop_config import is_uvloop_active, get_event_loop_info


async def test_sqlite_basic():
    """Test basic SQLite operations."""
    print("🗄️  Testing SQLite with Rust backend...")
    
    try:
        # Connect to SQLite
        connection_string = "sqlite:///test_oxen.db"
        print(f"🔗 Connection string: {connection_string}")
        
        # Try to connect
        print("🔄 Attempting to connect...")
        engine = await connect(connection_string)
        print("✅ Connection successful!")
        
        # Test basic query
        print("🔄 Testing basic query...")
        result = await engine.execute_query("SELECT 1 as test")
        print(f"📊 Query result: {result}")
        
        if result.get('error') is None:
            print("✅ Basic query successful!")
            
            # Test table creation
            print("🔄 Testing table creation...")
            create_result = await engine.create_table("test_users", {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "username": "TEXT UNIQUE NOT NULL",
                "email": "TEXT UNIQUE NOT NULL",
                "age": "INTEGER NOT NULL",
                "salary": "REAL NOT NULL"
            })
            print(f"📊 Create table result: {create_result}")
            
            if create_result is None or create_result.get('error') is None:
                print("✅ Table creation successful!")
                
                # Test insert
                print("🔄 Testing insert...")
                insert_result = await engine.insert_record("test_users", {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "age": 30,
                    "salary": 75000.0
                })
                print(f"📊 Insert result: {insert_result}")
                
                if insert_result.get('error') is None:
                    print("✅ Insert successful!")
                    
                    # Test select
                    print("🔄 Testing select...")
                    select_result = await engine.select_records("test_users")
                    print(f"📊 Select result: {select_result}")
                    
                    if select_result.get('error') is None:
                        print("✅ Select successful!")
                        data = select_result.get('data', [])
                        print(f"📊 Retrieved {len(data)} records")
                        for record in data:
                            print(f"   - {record}")
                    else:
                        print(f"❌ Select failed: {select_result.get('error')}")
                else:
                    print(f"❌ Insert failed: {insert_result.get('error')}")
            else:
                print(f"❌ Table creation failed: {create_result}")
        else:
            print(f"❌ Basic query failed: {result.get('error')}")
        
        # Cleanup
        await engine.drop_table("test_users")
        print("✅ Cleanup completed")
        
        return engine
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_window_functions_sqlite():
    """Test window functions with SQLite."""
    print("\n🪟 Testing Window Functions with SQLite...")
    
    try:
        # Connect to SQLite
        engine = await connect("sqlite:///test_window.db")
        
        # Create test table
        await engine.create_table("products", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "category": "TEXT NOT NULL",
            "price": "REAL NOT NULL",
            "stock": "INTEGER NOT NULL",
            "rating": "REAL"
        })
        
        # Insert test data
        products_data = [
            {"name": "Laptop", "category": "Electronics", "price": 1200.0, "stock": 50, "rating": 4.5},
            {"name": "Phone", "category": "Electronics", "price": 800.0, "stock": 100, "rating": 4.2},
            {"name": "Tablet", "category": "Electronics", "price": 600.0, "stock": 30, "rating": 4.0},
            {"name": "Book", "category": "Books", "price": 25.0, "stock": 200, "rating": 4.8},
            {"name": "Pen", "category": "Office", "price": 5.0, "stock": 500, "rating": 3.5},
        ]
        
        for product_data in products_data:
            await engine.insert_record("products", product_data)
        
        print("✅ Created products for window function testing")
        
        # Test window function (SQLite supports ROW_NUMBER)
        window_query = """
        SELECT 
            name,
            category,
            price,
            ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) as price_rank
        FROM products
        """
        window_result = await engine.execute_query(window_query)
        
        if window_result.get('error') is None:
            print("✅ Window function test successful")
            for row in window_result.get('data', []):
                print(f"   - {row['name']} ({row['category']}): ${row['price']} (Rank: {row['price_rank']})")
        else:
            print(f"❌ Window function test failed: {window_result.get('error')}")
        
        # Test CTE (SQLite supports CTEs)
        cte_query = """
        WITH product_stats AS (
            SELECT 
                category,
                COUNT(*) as product_count,
                AVG(price) as avg_price,
                MAX(price) as max_price
            FROM products
            GROUP BY category
        )
        SELECT * FROM product_stats
        """
        cte_result = await engine.execute_query(cte_query)
        
        if cte_result.get('error') is None:
            print("✅ CTE test successful")
            for row in cte_result.get('data', []):
                print(f"   - {row['category']}: {row['product_count']} products, avg ${row['avg_price']:.2f}")
        else:
            print(f"❌ CTE test failed: {cte_result.get('error')}")
        
        # Cleanup
        await engine.drop_table("products")
        await disconnect(engine)
        
    except Exception as e:
        print(f"❌ Window functions test failed: {e}")


async def main():
    """Main test function."""
    print("🚀 SQLite Basic Test with Rust Backend")
    print("=" * 50)
    
    # Print uvloop status
    loop_info = get_event_loop_info()
    print(f"📊 Event Loop Info: {loop_info}")
    print(f"🚀 uvloop active: {is_uvloop_active()}")
    
    # Run basic test
    engine = await test_sqlite_basic()
    
    if engine:
        print("\n" + "=" * 50)
        print("✅ Basic SQLite test completed!")
        
        # Cleanup
        await disconnect(engine)
        print("✅ Database disconnected")
        
        # Test window functions
        await test_window_functions_sqlite()
        
    else:
        print("\n❌ Basic SQLite test failed!")


if __name__ == "__main__":
    asyncio.run(main()) 