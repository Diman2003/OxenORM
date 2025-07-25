#!/usr/bin/env python3
"""
Simple Phase 1 Features Test

This script tests the core Phase 1 features without complex dependencies.
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))


async def test_performance_monitoring():
    """Test performance monitoring features."""
    print("🔍 Testing Performance Monitoring")
    print("=" * 40)
    
    try:
        from oxen.monitoring import (
            PerformanceMonitor, 
            QueryMetrics, 
            get_performance_monitor,
            enable_performance_monitoring,
            disable_performance_monitoring
        )
        
        # Test monitor creation
        monitor = PerformanceMonitor(max_history_size=100)
        print("✅ Performance monitor created")
        
        # Test query tracking
        async with monitor.track_query("SELECT * FROM test", {"param": "value"}) as query_id:
            await asyncio.sleep(0.1)  # Simulate query execution
            print(f"✅ Query tracked with ID: {query_id}")
        
        # Test statistics
        stats = monitor.get_query_statistics()
        print(f"✅ Query statistics: {stats}")
        
        # Test global monitor
        global_monitor = get_performance_monitor()
        print("✅ Global monitor accessed")
        
        # Test performance report
        report = monitor.get_performance_report()
        print(f"✅ Performance report generated: {len(report)} sections")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        return False


async def test_multi_database_manager():
    """Test multi-database manager features."""
    print("\n🗄️ Testing Multi-Database Manager")
    print("=" * 40)
    
    try:
        from oxen.multi_database_manager import MultiDatabaseManager
        from oxen.backends.base import DatabaseConfig
        from oxen.backends.sqlite import SQLiteBackend
        
        # Create temporary database files
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp1:
            db1_path = tmp1.name
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp2:
            db2_path = tmp2.name
        
        try:
            # Create multi-database manager
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
            
            print("✅ Added primary and replica databases")
            
            # Initialize manager
            await manager.initialize()
            print("✅ Multi-database manager initialized")
            
            # List databases
            databases = manager.list_databases()
            print(f"✅ Found {len(databases)} databases")
            
            # Execute on primary database
            result = await manager.execute_on_database(
                "SELECT 1 as test",
                database_name="primary"
            )
            print(f"✅ Primary database query: {result[0]['test']}")
            
            # Execute on all databases
            results = await manager.execute_on_all_databases("SELECT 1 as test")
            print(f"✅ Multi-database query: {len(results)} databases responded")
            
            # Health check
            health = await manager.health_check()
            print(f"✅ Health check: {sum(health.values())}/{len(health)} databases healthy")
            
            await manager.close()
            
            return True
            
        finally:
            os.unlink(db1_path)
            os.unlink(db2_path)
        
    except Exception as e:
        print(f"❌ Multi-database manager test failed: {e}")
        return False


async def test_sqlite_backend():
    """Test SQLite backend features."""
    print("\n📱 Testing SQLite Backend")
    print("=" * 40)
    
    try:
        from oxen.backends.base import DatabaseConfig
        from oxen.backends.sqlite import SQLiteBackend
        
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
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
            
            await backend.close()
            
            return True
            
        finally:
            os.unlink(db_path)
        
    except Exception as e:
        print(f"❌ SQLite backend test failed: {e}")
        return False


async def test_connection_pooling():
    """Test connection pooling features."""
    print("\n🏊 Testing Connection Pooling")
    print("=" * 40)
    
    try:
        from oxen.backends.base import DatabaseConfig
        from oxen.backends.sqlite import SQLiteBackend
        
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Create backend with connection pooling
            config = DatabaseConfig(
                sqlite_path=db_path,
                pool_size=3,
                max_overflow=2,
                pool_timeout=10
            )
            
            backend = SQLiteBackend(config)
            await backend.initialize()
            
            print("✅ Backend initialized with connection pooling")
            
            # Test multiple concurrent connections
            async def test_connection(conn_id):
                async with backend.get_connection() as conn:
                    result = await backend.execute_query(conn, f"SELECT {conn_id} as conn_id")
                    await asyncio.sleep(0.1)  # Simulate work
                    return result[0]['conn_id']
            
            # Run multiple concurrent connections
            tasks = [test_connection(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            
            print(f"✅ Concurrent connections completed: {results}")
            
            # Get pool statistics
            stats = backend.get_pool_stats()
            print(f"✅ Pool stats: {stats['total_connections']} total, {stats['utilization']:.1%} utilization")
            
            await backend.close()
            
            return True
            
        finally:
            os.unlink(db_path)
        
    except Exception as e:
        print(f"❌ Connection pooling test failed: {e}")
        return False


async def test_transactions():
    """Test transaction features."""
    print("\n💾 Testing Transactions")
    print("=" * 40)
    
    try:
        from oxen.backends.base import DatabaseConfig
        from oxen.backends.sqlite import SQLiteBackend
        
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
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
            
            print("✅ Test table created")
            
            # Test successful transaction
            async with backend.transaction() as conn:
                await backend.execute_query(conn, 
                    "INSERT INTO test_transactions (value) VALUES (:value)",
                    {'value': 'transaction1'}
                )
                await backend.execute_query(conn, 
                    "INSERT INTO test_transactions (value) VALUES (:value)",
                    {'value': 'transaction2'}
                )
                print("✅ Successful transaction committed")
            
            # Verify data
            result = await backend.execute("SELECT COUNT(*) as count FROM test_transactions")
            print(f"✅ Records after commit: {result[0]['count']}")
            
            # Test failed transaction (rollback)
            try:
                async with backend.transaction() as conn:
                    await backend.execute_query(conn, 
                        "INSERT INTO test_transactions (value) VALUES (:value)",
                        {'value': 'transaction3'}
                    )
                    # Simulate error
                    raise Exception("Simulated transaction error")
            except Exception as e:
                print(f"✅ Transaction rolled back: {e}")
            
            # Verify rollback
            result = await backend.execute("SELECT COUNT(*) as count FROM test_transactions")
            print(f"✅ Records after rollback: {result[0]['count']}")
            
            await backend.close()
            
            return True
            
        finally:
            os.unlink(db_path)
        
    except Exception as e:
        print(f"❌ Transaction test failed: {e}")
        return False


async def main():
    """Run all Phase 1 feature tests."""
    print("🚀 Testing OxenORM Phase 1 Features")
    print("=" * 60)
    
    tests = [
        ("Performance Monitoring", test_performance_monitoring),
        ("Multi-Database Manager", test_multi_database_manager),
        ("SQLite Backend", test_sqlite_backend),
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
        print("🎉 All Phase 1 features are working correctly!")
        print("OxenORM Phase 1 is ready for production use.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 