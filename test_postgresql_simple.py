#!/usr/bin/env python3
"""
Simple PostgreSQL test with Rust backend
Testing basic operations and advanced SQL features
"""

import asyncio
import time
from oxen import connect, disconnect
from oxen.uvloop_config import is_uvloop_active, get_event_loop_info


async def test_postgresql_basic():
    """Test basic PostgreSQL operations."""
    print("🗄️  Testing PostgreSQL with Rust backend...")
    
    try:
        # Connect to PostgreSQL
        connection_string = "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm"
        engine = await connect(connection_string)
        print("✅ PostgreSQL connected successfully")
        
        # Test basic query
        result = await engine.execute_query("SELECT version()")
        if result.get('error') is None:
            version = result.get('data', [{}])[0].get('version', 'Unknown')
            print(f"✅ PostgreSQL version: {version}")
        
        # Create a test table
        await engine.create_table("test_users", {
            "id": "SERIAL PRIMARY KEY",
            "username": "VARCHAR(100) UNIQUE NOT NULL",
            "email": "VARCHAR(255) UNIQUE NOT NULL",
            "age": "INTEGER NOT NULL",
            "salary": "DECIMAL(10,2) NOT NULL",
            "tags": "TEXT[]",
            "metadata": "JSONB"
        })
        print("✅ Test table created")
        
        # Insert test data
        test_users = [
            {"username": "john_doe", "email": "john@example.com", "age": 30, "salary": 75000.0, "tags": ["developer", "python"], "metadata": {"department": "engineering"}},
            {"username": "jane_smith", "email": "jane@example.com", "age": 28, "salary": 80000.0, "tags": ["designer", "ui"], "metadata": {"department": "design"}},
            {"username": "bob_wilson", "email": "bob@example.com", "age": 35, "salary": 90000.0, "tags": ["manager", "lead"], "metadata": {"department": "management"}},
        ]
        
        for user_data in test_users:
            result = await engine.insert_record("test_users", user_data)
            if result.get('error') is None:
                user_id = result.get('data', {}).get('id')
                print(f"✅ Created user: {user_data['username']} (ID: {user_id})")
            else:
                print(f"❌ Failed to create user {user_data['username']}: {result.get('error')}")
        
        # Test basic queries
        all_users = await engine.select_records("test_users")
        print(f"✅ Retrieved {len(all_users.get('data', []))} users")
        
        # Test window function
        window_query = """
        SELECT 
            username,
            salary,
            ROW_NUMBER() OVER (ORDER BY salary DESC) as salary_rank
        FROM test_users
        """
        window_result = await engine.execute_query(window_query)
        if window_result.get('error') is None:
            print("✅ Window function test successful")
            for row in window_result.get('data', []):
                print(f"   - {row['username']}: ${row['salary']} (Rank: {row['salary_rank']})")
        
        # Test CTE (Common Table Expression)
        cte_query = """
        WITH user_stats AS (
            SELECT 
                username,
                salary,
                age,
                CASE 
                    WHEN salary >= 80000 THEN 'High'
                    WHEN salary >= 70000 THEN 'Medium'
                    ELSE 'Low'
                END as salary_category
            FROM test_users
        )
        SELECT * FROM user_stats WHERE salary_category = 'High'
        """
        cte_result = await engine.execute_query(cte_query)
        if cte_result.get('error') is None:
            print("✅ CTE test successful")
            for row in cte_result.get('data', []):
                print(f"   - {row['username']}: {row['salary_category']} earner")
        
        # Test JSON operations
        json_query = """
        SELECT username, metadata->>'department' as department
        FROM test_users
        WHERE metadata IS NOT NULL
        """
        json_result = await engine.execute_query(json_query)
        if json_result.get('error') is None:
            print("✅ JSON operations test successful")
            for row in json_result.get('data', []):
                print(f"   - {row['username']}: {row['department']}")
        
        # Test array operations
        array_query = """
        SELECT username, tags
        FROM test_users
        WHERE 'python' = ANY(tags)
        """
        array_result = await engine.execute_query(array_query)
        if array_result.get('error') is None:
            print("✅ Array operations test successful")
            for row in array_result.get('data', []):
                print(f"   - {row['username']}: {row['tags']}")
        
        # Test performance
        print("\n⚡ Performance test...")
        start_time = time.time()
        
        # Bulk insert test
        bulk_users = []
        for i in range(50):
            bulk_users.append({
                "username": f"perf_user_{i}",
                "email": f"perf{i}@example.com",
                "age": 20 + (i % 50),
                "salary": 50000.0 + (i * 100),
                "tags": ["performance", f"batch_{i//10}"],
                "metadata": {"batch": i//10}
            })
        
        # Insert one by one for now (bulk_insert not implemented yet)
        for user_data in bulk_users:
            await engine.insert_record("test_users", user_data)
        
        insert_time = time.time() - start_time
        print(f"✅ Inserted {len(bulk_users)} users in {insert_time:.4f}s")
        
        # Query performance test
        start_time = time.time()
        perf_result = await engine.execute_query(
            "SELECT COUNT(*) as total_users FROM test_users"
        )
        query_time = time.time() - start_time
        total_users = perf_result.get('data', [{}])[0].get('total_users', 0)
        print(f"✅ Counted {total_users} users in {query_time:.4f}s")
        
        # Cleanup
        await engine.drop_table("test_users")
        print("✅ Test table dropped")
        
        return engine
        
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return None


async def main():
    """Main test function."""
    print("🚀 PostgreSQL Simple Test with Rust Backend")
    print("=" * 60)
    
    # Print uvloop status
    loop_info = get_event_loop_info()
    print(f"📊 Event Loop Info: {loop_info}")
    print(f"🚀 uvloop active: {is_uvloop_active()}")
    
    # Run test
    engine = await test_postgresql_basic()
    
    if engine:
        print("\n" + "=" * 60)
        print("✅ PostgreSQL test completed successfully!")
        
        # Cleanup
        await disconnect(engine)
        print("✅ Database disconnected")
    else:
        print("\n❌ PostgreSQL test failed!")


if __name__ == "__main__":
    asyncio.run(main()) 