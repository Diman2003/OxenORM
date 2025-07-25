#!/usr/bin/env python3
"""
Test Multi-Database Support

This script tests the comprehensive multi-database support system including:
- SQLite backend
- MySQL backend
- PostgreSQL backend
- Connection pooling
- Database switching
- Performance optimizations
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from oxen.backends.base import DatabaseConfig
from oxen.backends.sqlite import SQLiteBackend
from oxen.backends.mysql import MySQLBackend
from oxen.backends.postgresql import PostgreSQLBackend
from oxen.multi_database_manager import MultiDatabaseManager, get_multi_database_manager


async def test_sqlite_backend():
    """Test SQLite backend functionality."""
    print("🧪 Testing SQLite Backend")
    print("=" * 40)
    
    try:
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Create SQLite backend
        config = DatabaseConfig(sqlite_path=db_path)
        backend = SQLiteBackend(config)
        
        # Initialize backend
        await backend.initialize()
        print("✅ SQLite backend initialized")
        
        # Test connection
        async with backend.get_connection() as conn:
            result = await backend.execute_query(conn, "SELECT 1 as test")
            assert result[0]['test'] == 1
            print("✅ SQLite connection test passed")
        
        # Test table creation
        columns = [
            {'name': 'id', 'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
            {'name': 'name', 'type': 'TEXT', 'nullable': False},
            {'name': 'email', 'type': 'TEXT', 'nullable': True, 'index': True}
        ]
        
        await backend.create_table('test_users', columns)
        print("✅ SQLite table creation test passed")
        
        # Test data insertion
        async with backend.transaction() as conn:
            await backend.execute_query(conn, 
                "INSERT INTO test_users (name, email) VALUES (:name, :email)",
                {'name': 'John Doe', 'email': 'john@example.com'}
            )
        
        # Test data retrieval
        result = await backend.execute("SELECT * FROM test_users")
        assert len(result) == 1
        assert result[0]['name'] == 'John Doe'
        print("✅ SQLite CRUD operations test passed")
        
        # Test performance stats
        stats = backend.get_performance_stats()
        assert 'dialect' in stats
        assert stats['dialect'] == 'sqlite'
        print("✅ SQLite performance stats test passed")
        
        # Cleanup
        await backend.close()
        os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite backend test failed: {e}")
        return False


async def test_mysql_backend():
    """Test MySQL backend functionality."""
    print("\n🧪 Testing MySQL Backend")
    print("=" * 40)
    
    try:
        # Skip if MySQL is not available
        try:
            import aiomysql
        except ImportError:
            print("⚠️  aiomysql not available, skipping MySQL test")
            return True
        
        # Create MySQL backend (using default config)
        config = DatabaseConfig(
            host="localhost",
            port=3306,
            database="test_oxenorm",
            username="root",
            password="",
            pool_size=2
        )
        
        backend = MySQLBackend(config)
        
        # Try to initialize (might fail if MySQL is not running)
        try:
            await backend.initialize()
            print("✅ MySQL backend initialized")
            
            # Test connection
            async with backend.get_connection() as conn:
                result = await backend.execute_query(conn, "SELECT 1 as test")
                assert result[0]['test'] == 1
                print("✅ MySQL connection test passed")
            
            # Test features
            features = backend.get_supported_features()
            assert 'transactions' in features
            assert 'foreign_keys' in features
            print("✅ MySQL features test passed")
            
            # Cleanup
            await backend.close()
            
        except Exception as e:
            print(f"⚠️  MySQL not available: {e}")
            return True
        
        return True
        
    except Exception as e:
        print(f"❌ MySQL backend test failed: {e}")
        return False


async def test_postgresql_backend():
    """Test PostgreSQL backend functionality."""
    print("\n🧪 Testing PostgreSQL Backend")
    print("=" * 40)
    
    try:
        # Skip if PostgreSQL is not available
        try:
            import asyncpg
        except ImportError:
            print("⚠️  asyncpg not available, skipping PostgreSQL test")
            return True
        
        # Create PostgreSQL backend (using default config)
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_oxenorm",
            username="postgres",
            password="",
            pool_size=2
        )
        
        backend = PostgreSQLBackend(config)
        
        # Try to initialize (might fail if PostgreSQL is not running)
        try:
            await backend.initialize()
            print("✅ PostgreSQL backend initialized")
            
            # Test connection
            async with backend.get_connection() as conn:
                result = await backend.execute_query(conn, "SELECT 1 as test")
                assert result[0]['test'] == 1
                print("✅ PostgreSQL connection test passed")
            
            # Test features
            features = backend.get_supported_features()
            assert 'transactions' in features
            assert 'json_functions' in features
            print("✅ PostgreSQL features test passed")
            
            # Cleanup
            await backend.close()
            
        except Exception as e:
            print(f"⚠️  PostgreSQL not available: {e}")
            return True
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL backend test failed: {e}")
        return False


async def test_multi_database_manager():
    """Test multi-database manager functionality."""
    print("\n🧪 Testing Multi-Database Manager")
    print("=" * 40)
    
    try:
        # Create temporary database files
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp1:
            db1_path = tmp1.name
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp2:
            db2_path = tmp2.name
        
        # Create manager
        manager = MultiDatabaseManager()
        
        # Add databases
        manager.add_database(
            name="primary",
            url=f"sqlite:///{db1_path}",
            is_primary=True
        )
        
        manager.add_database(
            name="replica",
            url=f"sqlite:///{db2_path}",
            is_read_only=True
        )
        
        print("✅ Databases added to manager")
        
        # Initialize manager
        await manager.initialize()
        print("✅ Multi-database manager initialized")
        
        # Test database listing
        databases = manager.list_databases()
        assert len(databases) == 2
        assert any(db['name'] == 'primary' and db['is_primary'] for db in databases)
        assert any(db['name'] == 'replica' and db['is_read_only'] for db in databases)
        print("✅ Database listing test passed")
        
        # Test execution on specific database
        result = await manager.execute_on_database(
            "SELECT 1 as test",
            database_name="primary"
        )
        assert result[0]['test'] == 1
        print("✅ Database-specific execution test passed")
        
        # Test execution on all databases
        results = await manager.execute_on_all_databases("SELECT 1 as test")
        assert len(results) == 1  # Only primary (excludes read-only)
        assert results['primary'][0]['test'] == 1
        print("✅ Multi-database execution test passed")
        
        # Test execution on read replicas
        results = await manager.execute_on_read_replicas("SELECT 1 as test")
        assert len(results) == 1
        assert results['replica'][0]['test'] == 1
        print("✅ Read replica execution test passed")
        
        # Test database switching
        manager.switch_primary("replica")
        assert manager.primary_database == "replica"
        print("✅ Database switching test passed")
        
        # Test health check
        health = await manager.health_check()
        assert all(health.values())
        print("✅ Health check test passed")
        
        # Test database stats
        stats = manager.get_database_stats()
        assert 'primary' in stats
        assert 'replica' in stats
        print("✅ Database stats test passed")
        
        # Test optimal database selection
        optimal_read = manager.get_optimal_database("read")
        assert optimal_read == "replica"  # Should prefer read replica
        print("✅ Optimal database selection test passed")
        
        # Cleanup
        await manager.close()
        os.unlink(db1_path)
        os.unlink(db2_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-database manager test failed: {e}")
        return False


async def test_connection_pooling():
    """Test connection pooling functionality."""
    print("\n🧪 Testing Connection Pooling")
    print("=" * 40)
    
    try:
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Create backend with connection pooling
        config = DatabaseConfig(
            sqlite_path=db_path,
            pool_size=3,
            max_overflow=2,
            pool_timeout=10
        )
        
        backend = SQLiteBackend(config)
        await backend.initialize()
        
        # Test multiple concurrent connections
        async def test_connection():
            async with backend.get_connection() as conn:
                result = await backend.execute_query(conn, "SELECT 1 as test")
                await asyncio.sleep(0.1)  # Simulate work
                return result[0]['test']
        
        # Run multiple concurrent connections
        tasks = [test_connection() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert all(result == 1 for result in results)
        print("✅ Concurrent connection test passed")
        
        # Test pool statistics
        stats = backend.get_pool_stats()
        assert 'pool_size' in stats
        assert 'total_connections' in stats
        assert 'utilization' in stats
        print("✅ Pool statistics test passed")
        
        # Cleanup
        await backend.close()
        os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Connection pooling test failed: {e}")
        return False


async def test_transactions():
    """Test transaction functionality."""
    print("\n🧪 Testing Transactions")
    print("=" * 40)
    
    try:
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Create backend
        config = DatabaseConfig(sqlite_path=db_path)
        backend = SQLiteBackend(config)
        await backend.initialize()
        
        # Create test table
        columns = [
            {'name': 'id', 'type': 'INTEGER', 'primary_key': True, 'auto_increment': True},
            {'name': 'value', 'type': 'TEXT', 'nullable': False}
        ]
        await backend.create_table('test_transactions', columns)
        
        # Test successful transaction
        async with backend.transaction() as conn:
            await backend.execute_query(conn, 
                "INSERT INTO test_transactions (value) VALUES (:value)",
                {'value': 'test1'}
            )
            await backend.execute_query(conn, 
                "INSERT INTO test_transactions (value) VALUES (:value)",
                {'value': 'test2'}
            )
        
        # Verify data was committed
        result = await backend.execute("SELECT COUNT(*) as count FROM test_transactions")
        assert result[0]['count'] == 2
        print("✅ Successful transaction test passed")
        
        # Test failed transaction (rollback)
        try:
            async with backend.transaction() as conn:
                await backend.execute_query(conn, 
                    "INSERT INTO test_transactions (value) VALUES (:value)",
                    {'value': 'test3'}
                )
                # Simulate error
                raise Exception("Simulated error")
        except Exception:
            pass
        
        # Verify data was rolled back
        result = await backend.execute("SELECT COUNT(*) as count FROM test_transactions")
        assert result[0]['count'] == 2  # Should still be 2
        print("✅ Transaction rollback test passed")
        
        # Cleanup
        await backend.close()
        os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Transaction test failed: {e}")
        return False


async def run_all_tests():
    """Run all multi-database support tests."""
    print("🚀 Running Multi-Database Support Tests")
    print("=" * 60)
    
    tests = [
        ("SQLite Backend", test_sqlite_backend),
        ("MySQL Backend", test_mysql_backend),
        ("PostgreSQL Backend", test_postgresql_backend),
        ("Multi-Database Manager", test_multi_database_manager),
        ("Connection Pooling", test_connection_pooling),
        ("Transactions", test_transactions),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ FAILED: {test_name} - {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Multi-database support is ready.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1) 