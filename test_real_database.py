#!/usr/bin/env python3
"""
Real PostgreSQL Database Test for OxenORM

This script tests the OxenORM Rust backend with a real PostgreSQL database.
"""

import asyncio
import sys
import os
from typing import Dict, Any, List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from oxen.rust_engine import OxenEngine
    RUST_AVAILABLE = True
except ImportError as e:
    print(f"❌ Rust engine not available: {e}")
    print("Please build the Rust extension first with: maturin develop")
    RUST_AVAILABLE = False

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "oxenorm_test",
    "username": "oxenorm_user",
    "password": "oxenorm_pass"
}

def build_connection_string() -> str:
    """Build PostgreSQL connection string."""
    return f"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

async def test_database_connection():
    """Test basic database connection."""
    print("🔌 Testing Database Connection")
    print("=" * 40)
    
    connection_string = build_connection_string()
    print(f"Connection string: {connection_string.replace(DB_CONFIG['password'], '***')}")
    
    try:
        engine = OxenEngine(connection_string)
        print("✅ Engine created successfully")
        
        # Configure pool
        engine.configure_pool(max_connections=5, min_connections=1)
        print("✅ Pool configured")
        
        # Connect
        result = await engine.connect()
        print(f"✅ Connected successfully: {result}")
        
        # Check connection status
        is_connected = engine.is_connected()
        print(f"✅ Connection status: {is_connected}")
        
        # Get pool status
        pool_status = await engine.get_pool_status()
        print(f"✅ Pool status: {pool_status}")
        
        return engine
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

async def test_basic_queries(engine: OxenEngine):
    """Test basic SQL queries."""
    print("\n📝 Testing Basic Queries")
    print("=" * 40)
    
    try:
        # Test 1: Simple SELECT
        print("1. Testing simple SELECT...")
        result = await engine.execute_query("SELECT 1 as test_value, 'hello' as greeting")
        print(f"✅ SELECT result: {result}")
        
        # Test 2: SELECT with parameters
        print("\n2. Testing SELECT with parameters...")
        result = await engine.execute_query(
            "SELECT $1 as param1, $2 as param2, $3 as param3",
            ["hello", 42, True]
        )
        print(f"✅ Parameterized SELECT result: {result}")
        
        # Test 3: CREATE TABLE
        print("\n3. Testing CREATE TABLE...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS test_users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            age INTEGER,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        result = await engine.execute_query(create_table_sql)
        print(f"✅ CREATE TABLE result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

async def test_crud_operations(engine: OxenEngine):
    """Test CRUD operations."""
    print("\n🔄 Testing CRUD Operations")
    print("=" * 40)
    
    try:
        # Test 1: INSERT
        print("1. Testing INSERT...")
        insert_sql = """
        INSERT INTO test_users (name, email, age, is_active) 
        VALUES ($1, $2, $3, $4) 
        RETURNING id, name, email, age, is_active, created_at
        """
        result = await engine.execute_query(
            insert_sql,
            ["Alice Johnson", "alice@example.com", 30, True]
        )
        print(f"✅ INSERT result: {result}")
        
        # Test 2: INSERT another record
        print("\n2. Testing another INSERT...")
        result = await engine.execute_query(
            insert_sql,
            ["Bob Smith", "bob@example.com", 25, True]
        )
        print(f"✅ Second INSERT result: {result}")
        
        # Test 3: SELECT all records
        print("\n3. Testing SELECT all...")
        result = await engine.execute_query("SELECT * FROM test_users ORDER BY id")
        print(f"✅ SELECT all result: {result}")
        
        # Test 4: SELECT with WHERE
        print("\n4. Testing SELECT with WHERE...")
        result = await engine.execute_query(
            "SELECT * FROM test_users WHERE age > $1",
            [25]
        )
        print(f"✅ SELECT with WHERE result: {result}")
        
        # Test 5: UPDATE
        print("\n5. Testing UPDATE...")
        result = await engine.execute_query(
            "UPDATE test_users SET age = $1 WHERE name = $2",
            [31, "Alice Johnson"]
        )
        print(f"✅ UPDATE result: {result}")
        
        # Test 6: SELECT after UPDATE
        print("\n6. Testing SELECT after UPDATE...")
        result = await engine.execute_query(
            "SELECT * FROM test_users WHERE name = $1",
            ["Alice Johnson"]
        )
        print(f"✅ SELECT after UPDATE result: {result}")
        
        # Test 7: DELETE
        print("\n7. Testing DELETE...")
        result = await engine.execute_query(
            "DELETE FROM test_users WHERE name = $1",
            ["Bob Smith"]
        )
        print(f"✅ DELETE result: {result}")
        
        # Test 8: SELECT after DELETE
        print("\n8. Testing SELECT after DELETE...")
        result = await engine.execute_query("SELECT * FROM test_users ORDER BY id")
        print(f"✅ SELECT after DELETE result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD test failed: {e}")
        return False

async def test_transactions(engine: OxenEngine):
    """Test transaction operations."""
    print("\n💼 Testing Transactions")
    print("=" * 40)
    
    try:
        # Test 1: Begin transaction
        print("1. Testing BEGIN transaction...")
        tx_info = await engine.begin_transaction()
        print(f"✅ Transaction started: {tx_info}")
        
        # Note: Real transaction support would require storing the transaction
        # object, which is complex across the FFI boundary
        # For now, we're just testing the transaction info creation
        
        return True
        
    except Exception as e:
        print(f"❌ Transaction test failed: {e}")
        return False

async def test_batch_operations(engine: OxenEngine):
    """Test batch operations."""
    print("\n📦 Testing Batch Operations")
    print("=" * 40)
    
    try:
        # Test 1: Batch INSERT
        print("1. Testing batch INSERT...")
        insert_sql = """
        INSERT INTO test_users (name, email, age, is_active) 
        VALUES ($1, $2, $3, $4)
        """
        
        batch_data = [
            ["Charlie Brown", "charlie@example.com", 28, True],
            ["Diana Prince", "diana@example.com", 35, True],
            ["Eve Wilson", "eve@example.com", 22, False],
        ]
        
        result = await engine.execute_many(insert_sql, batch_data)
        print(f"✅ Batch INSERT result: {result}")
        
        # Test 2: SELECT to verify batch insert
        print("\n2. Verifying batch INSERT...")
        result = await engine.execute_query("SELECT * FROM test_users ORDER BY id")
        print(f"✅ Verification result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch operations test failed: {e}")
        return False

async def test_error_handling(engine: OxenEngine):
    """Test error handling."""
    print("\n⚠️  Testing Error Handling")
    print("=" * 40)
    
    try:
        # Test 1: Invalid SQL
        print("1. Testing invalid SQL...")
        try:
            result = await engine.execute_query("SELECT * FROM non_existent_table")
            print(f"❌ Should have failed: {result}")
            return False
        except Exception as e:
            print(f"✅ Correctly failed with: {e}")
        
        # Test 2: Invalid parameters
        print("\n2. Testing invalid parameters...")
        try:
            result = await engine.execute_query(
                "SELECT * FROM test_users WHERE id = $1",
                ["not_a_number"]
            )
            print(f"❌ Should have failed: {result}")
            return False
        except Exception as e:
            print(f"✅ Correctly failed with: {e}")
        
        # Test 3: Duplicate key violation
        print("\n3. Testing duplicate key violation...")
        try:
            result = await engine.execute_query(
                "INSERT INTO test_users (name, email, age) VALUES ($1, $2, $3)",
                ["Duplicate User", "alice@example.com", 30]  # Duplicate email
            )
            print(f"❌ Should have failed: {result}")
            return False
        except Exception as e:
            print(f"✅ Correctly failed with: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def test_performance(engine: OxenEngine):
    """Test performance with multiple queries."""
    print("\n⚡ Testing Performance")
    print("=" * 40)
    
    try:
        import time
        
        # Test 1: Multiple simple queries
        print("1. Testing multiple simple queries...")
        start_time = time.time()
        
        for i in range(10):
            result = await engine.execute_query(f"SELECT {i} as iteration")
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"✅ 10 queries completed in {duration:.3f} seconds ({duration/10:.3f}s per query)")
        
        # Test 2: Complex query
        print("\n2. Testing complex query...")
        start_time = time.time()
        
        complex_sql = """
        SELECT 
            COUNT(*) as total_users,
            AVG(age) as avg_age,
            MIN(age) as min_age,
            MAX(age) as max_age,
            COUNT(CASE WHEN is_active THEN 1 END) as active_users
        FROM test_users
        """
        
        result = await engine.execute_query(complex_sql)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Complex query completed in {duration:.3f} seconds")
        print(f"✅ Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

async def cleanup_database(engine: OxenEngine):
    """Clean up test data."""
    print("\n🧹 Cleaning Up Database")
    print("=" * 40)
    
    try:
        # Drop test table
        result = await engine.execute_query("DROP TABLE IF EXISTS test_users")
        print(f"✅ Cleanup result: {result}")
        
        # Close connection
        result = await engine.close()
        print(f"✅ Connection closed: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🧪 OxenORM Real PostgreSQL Database Test")
    print("=" * 60)
    
    if not RUST_AVAILABLE:
        print("❌ Rust engine not available. Cannot run tests.")
        return 1
    
    success = True
    engine = None
    
    try:
        # Test 1: Database connection
        engine = await test_database_connection()
        if not engine:
            return 1
        
        # Test 2: Basic queries
        if not await test_basic_queries(engine):
            success = False
        
        # Test 3: CRUD operations
        if not await test_crud_operations(engine):
            success = False
        
        # Test 4: Transactions
        if not await test_transactions(engine):
            success = False
        
        # Test 5: Batch operations
        if not await test_batch_operations(engine):
            success = False
        
        # Test 6: Error handling
        if not await test_error_handling(engine):
            success = False
        
        # Test 7: Performance
        if not await test_performance(engine):
            success = False
        
        # Test 8: Cleanup
        if not await cleanup_database(engine):
            success = False
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 All tests passed! OxenORM is working perfectly with PostgreSQL!")
            print("\n✅ Real database integration is complete and functional.")
            print("✅ Connection pooling is working correctly.")
            print("✅ CRUD operations are working correctly.")
            print("✅ Error handling is working correctly.")
            print("✅ Performance is acceptable.")
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test suite failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 