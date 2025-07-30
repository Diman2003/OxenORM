#!/usr/bin/env python3
"""
Advanced PostgreSQL test with window functions and CTEs using Rust backend
"""

import asyncio
from oxen.rust_bridge import OxenEngine


async def test_postgresql_advanced():
    """Test PostgreSQL advanced features with Rust backend."""
    print("🗄️  Testing PostgreSQL Advanced Features with Rust Backend...")
    
    connection_string = "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm"
    print(f"🔗 Connection string: {connection_string}")
    
    try:
        # Create Rust engine
        rust_engine = OxenEngine(connection_string)
        print("✅ Rust engine created")
        
        # Connect
        result = await rust_engine.connect()
        print(f"📊 Connect result: {result}")
        
        if result.get('error') is None:
            print("✅ Connection successful!")
            
            # Test table creation
            print("\n🔄 Creating test table...")
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock INTEGER NOT NULL,
                rating DECIMAL(3,2)
            )
            """
            create_result = await rust_engine.execute_query(create_table_sql)
            print(f"📊 Create table result: {create_result}")
            
            if create_result.get('error') is None:
                print("✅ Table creation successful!")
                
                # Insert test data
                print("\n🔄 Inserting test data...")
                insert_data = [
                    ("Laptop", "Electronics", 1200.00, 50, 4.5),
                    ("Phone", "Electronics", 800.00, 100, 4.2),
                    ("Tablet", "Electronics", 600.00, 30, 4.0),
                    ("Book", "Books", 25.00, 200, 4.8),
                    ("Pen", "Office", 5.00, 500, 3.5),
                ]
                
                for name, category, price, stock, rating in insert_data:
                    insert_sql = """
                    INSERT INTO products (name, category, price, stock, rating)
                    VALUES ($1, $2, $3, $4, $5)
                    """
                    insert_result = await rust_engine.execute_query(insert_sql, [name, category, price, stock, rating])
                    if insert_result.get('error') is None:
                        print(f"✅ Inserted: {name}")
                    else:
                        print(f"❌ Failed to insert {name}: {insert_result.get('error')}")
                
                # Test Window Functions
                print("\n🪟 Testing Window Functions...")
                window_query = """
                SELECT 
                    name,
                    category,
                    price,
                    ROW_NUMBER() OVER (PARTITION BY category ORDER BY price DESC) as price_rank,
                    RANK() OVER (ORDER BY price DESC) as overall_rank,
                    DENSE_RANK() OVER (ORDER BY rating DESC) as rating_rank
                FROM products
                ORDER BY category, price DESC
                """
                window_result = await rust_engine.execute_query(window_query)
                
                if window_result.get('error') is None:
                    print("✅ Window functions test successful!")
                    data = window_result.get('data', [])
                    for row in data:
                        print(f"   - {row['name']} ({row['category']}): ${row['price']} (Rank: {row['price_rank']}, Overall: {row['overall_rank']}, Rating: {row['rating_rank']})")
                else:
                    print(f"❌ Window functions test failed: {window_result.get('error')}")
                
                # Test CTEs (Common Table Expressions)
                print("\n📊 Testing CTEs...")
                cte_query = """
                WITH product_stats AS (
                    SELECT 
                        category,
                        COUNT(*) as product_count,
                        AVG(price) as avg_price,
                        MAX(price) as max_price,
                        MIN(price) as min_price,
                        SUM(stock) as total_stock
                    FROM products
                    GROUP BY category
                ),
                category_ranking AS (
                    SELECT 
                        category,
                        product_count,
                        avg_price,
                        max_price,
                        min_price,
                        total_stock,
                        ROW_NUMBER() OVER (ORDER BY avg_price DESC) as price_rank
                    FROM product_stats
                )
                SELECT * FROM category_ranking
                ORDER BY price_rank
                """
                cte_result = await rust_engine.execute_query(cte_query)
                
                if cte_result.get('error') is None:
                    print("✅ CTE test successful!")
                    data = cte_result.get('data', [])
                    for row in data:
                        print(f"   - {row['category']}: {row['product_count']} products, avg ${row['avg_price']:.2f}, stock {row['total_stock']}")
                else:
                    print(f"❌ CTE test failed: {cte_result.get('error')}")
                
                # Test JSON Operations (PostgreSQL specific)
                print("\n📄 Testing JSON Operations...")
                json_query = """
                SELECT 
                    name,
                    category,
                    price,
                    json_build_object(
                        'name', name,
                        'category', category,
                        'price', price,
                        'stock', stock,
                        'rating', rating
                    ) as product_json
                FROM products
                WHERE category = 'Electronics'
                """
                json_result = await rust_engine.execute_query(json_query)
                
                if json_result.get('error') is None:
                    print("✅ JSON operations test successful!")
                    data = json_result.get('data', [])
                    for row in data:
                        print(f"   - {row['name']}: {row['product_json']}")
                else:
                    print(f"❌ JSON operations test failed: {json_result.get('error')}")
                
                # Test Array Operations (PostgreSQL specific)
                print("\n📋 Testing Array Operations...")
                array_query = """
                SELECT 
                    category,
                    array_agg(name ORDER BY price DESC) as product_names,
                    array_agg(price ORDER BY price DESC) as prices
                FROM products
                GROUP BY category
                """
                array_result = await rust_engine.execute_query(array_query)
                
                if array_result.get('error') is None:
                    print("✅ Array operations test successful!")
                    data = array_result.get('data', [])
                    for row in data:
                        print(f"   - {row['category']}: {row['product_names']} at prices {row['prices']}")
                else:
                    print(f"❌ Array operations test failed: {array_result.get('error')}")
                
                # Cleanup
                print("\n🧹 Cleaning up...")
                drop_result = await rust_engine.execute_query("DROP TABLE IF EXISTS products")
                if drop_result.get('error') is None:
                    print("✅ Cleanup successful!")
                else:
                    print(f"❌ Cleanup failed: {drop_result.get('error')}")
                
            else:
                print(f"❌ Table creation failed: {create_result.get('error')}")
        else:
            print(f"❌ Connection failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 PostgreSQL Advanced Features Test with Rust Backend")
    print("=" * 60)
    
    await test_postgresql_advanced()


if __name__ == "__main__":
    asyncio.run(main()) 