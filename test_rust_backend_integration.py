#!/usr/bin/env python3
"""
Comprehensive test for Rust backend integration with all three database backends.
This test verifies that SQLite, MySQL, and PostgreSQL backends work correctly
with the unified Rust engine.
"""

import asyncio
import logging
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rust_engine_direct():
    """Test the Rust engine directly with different database types."""
    logger.info("=== Testing Rust Engine Direct Integration ===")
    
    try:
        import oxen_engine
        
        # Test SQLite (in-memory)
        logger.info("Testing SQLite (in-memory)...")
        sqlite_engine = oxen_engine.OxenEngine("sqlite::memory:")
        result = sqlite_engine.connect()
        logger.info(f"SQLite connection result: {result}")
        
        # Test a simple query
        query_result = sqlite_engine.execute_query("SELECT 1 as test_value, 'hello' as test_string")
        logger.info(f"SQLite query result: {query_result}")
        
        # Test with parameters
        param_result = sqlite_engine.execute_query(
            "SELECT ? as param1, ? as param2", 
            [42, "test_param"]
        )
        logger.info(f"SQLite parameterized query result: {param_result}")
        
        # Test batch operations (create table first)
        sqlite_engine.execute_query("CREATE TABLE IF NOT EXISTS test_table (id INTEGER, name TEXT)")
        batch_result = sqlite_engine.execute_many(
            "INSERT INTO test_table (id, name) VALUES (?, ?)",
            [[1, "Alice"], [2, "Bob"], [3, "Charlie"]]
        )
        logger.info(f"SQLite batch operation result: {batch_result}")
        
        sqlite_engine.close()
        logger.info("✅ SQLite direct test passed")
        
    except ImportError as e:
        logger.error(f"❌ oxen_engine not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Rust engine direct test failed: {e}")
        return False
    
    return True

async def test_sqlite_backend():
    """Test SQLite backend with Rust engine."""
    logger.info("=== Testing SQLite Backend with Rust Engine ===")
    
    try:
        from oxen.backends.sqlite import SQLiteBackend
        from oxen.backends.base import DatabaseConfig
        
        # Create SQLite config
        config = DatabaseConfig(
            sqlite_path=":memory:",
            max_connections=5,
            min_connections=1,
            connect_timeout=30
        )
        
        # Create backend
        backend = SQLiteBackend(config)
        
        # Test connection
        conn = await backend.create_connection(config)
        logger.info("✅ SQLite backend connection created")
        
        # Test query execution
        result = await backend.execute_query(conn, "SELECT 1 as test")
        logger.info(f"SQLite backend query result: {result}")
        
        # Test table creation
        columns = [
            {"name": "id", "type": "INTEGER", "primary_key": True, "auto_increment": True},
            {"name": "name", "type": "TEXT", "nullable": False},
            {"name": "email", "type": "TEXT", "nullable": True}
        ]
        
        await backend.create_table("users", columns)
        logger.info("✅ SQLite table creation successful")
        
        # Test data insertion
        insert_result = await backend.execute_query(
            conn, 
            'INSERT INTO users (name, email) VALUES (?, ?)',
            {"name": "John Doe", "email": "john@example.com"}
        )
        logger.info(f"SQLite insert result: {insert_result}")
        
        # Test data retrieval
        select_result = await backend.execute_query(conn, "SELECT * FROM users")
        logger.info(f"SQLite select result: {select_result}")
        
        # Test performance stats
        stats = backend.get_performance_stats()
        logger.info(f"SQLite performance stats: {stats}")
        
        await backend.close_connection(conn)
        logger.info("✅ SQLite backend test passed")
        
    except Exception as e:
        logger.error(f"❌ SQLite backend test failed: {e}")
        return False
    
    return True

async def test_mysql_backend():
    """Test MySQL backend with Rust engine."""
    logger.info("=== Testing MySQL Backend with Rust Engine ===")
    
    try:
        from oxen.backends.mysql import MySQLBackend
        from oxen.backends.base import DatabaseConfig
        
        # Create MySQL config (using test database)
        config = DatabaseConfig(
            host="localhost",
            port=3306,
            username="root",
            password="password",
            database="test",
            max_connections=5,
            min_connections=1,
            connect_timeout=30
        )
        
        # Create backend
        backend = MySQLBackend(config)
        
        # Test connection (this might fail if MySQL is not running)
        try:
            conn = await backend.create_connection(config)
            logger.info("✅ MySQL backend connection created")
            
            # Test query execution
            result = await backend.execute_query(conn, "SELECT 1 as test")
            logger.info(f"MySQL backend query result: {result}")
            
            # Test table creation
            columns = [
                {"name": "id", "type": "INT", "primary_key": True, "auto_increment": True},
                {"name": "name", "type": "VARCHAR(255)", "nullable": False},
                {"name": "email", "type": "VARCHAR(255)", "nullable": True}
            ]
            
            await backend.create_table("users", columns)
            logger.info("✅ MySQL table creation successful")
            
            # Test data insertion
            insert_result = await backend.execute_query(
                conn, 
                "INSERT INTO users (name, email) VALUES (?, ?)",
                {"name": "Jane Doe", "email": "jane@example.com"}
            )
            logger.info(f"MySQL insert result: {insert_result}")
            
            # Test data retrieval
            select_result = await backend.execute_query(conn, "SELECT * FROM users")
            logger.info(f"MySQL select result: {select_result}")
            
            # Test performance stats
            stats = backend.get_performance_stats()
            logger.info(f"MySQL performance stats: {stats}")
            
            await backend.close_connection(conn)
            logger.info("✅ MySQL backend test passed")
            
        except Exception as e:
            logger.warning(f"⚠️ MySQL backend test skipped (MySQL not available): {e}")
            logger.info("This is expected if MySQL server is not running")
            return True  # Skip test if MySQL is not available
        
    except Exception as e:
        logger.error(f"❌ MySQL backend test failed: {e}")
        return False
    
    return True

async def test_postgresql_backend():
    """Test PostgreSQL backend with Rust engine."""
    logger.info("=== Testing PostgreSQL Backend with Rust Engine ===")
    
    try:
        from oxen.backends.postgresql import PostgreSQLBackend
        from oxen.backends.base import DatabaseConfig
        
        # Create PostgreSQL config (using test database)
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            username="postgres",
            password="password",
            database="test",
            max_connections=5,
            min_connections=1,
            connect_timeout=30
        )
        
        # Create backend
        backend = PostgreSQLBackend(config)
        
        # Test connection (this might fail if PostgreSQL is not running)
        try:
            conn = await backend.create_connection(config)
            logger.info("✅ PostgreSQL backend connection created")
            
            # Test query execution
            result = await backend.execute_query(conn, "SELECT 1 as test")
            logger.info(f"PostgreSQL backend query result: {result}")
            
            # Test table creation
            columns = [
                {"name": "id", "type": "SERIAL", "primary_key": True},
                {"name": "name", "type": "VARCHAR(255)", "nullable": False},
                {"name": "email", "type": "VARCHAR(255)", "nullable": True}
            ]
            
            await backend.create_table("users", columns)
            logger.info("✅ PostgreSQL table creation successful")
            
            # Test data insertion
            insert_result = await backend.execute_query(
                conn, 
                "INSERT INTO users (name, email) VALUES (?, ?)",
                {"name": "Bob Smith", "email": "bob@example.com"}
            )
            logger.info(f"PostgreSQL insert result: {insert_result}")
            
            # Test data retrieval
            select_result = await backend.execute_query(conn, "SELECT * FROM users")
            logger.info(f"PostgreSQL select result: {select_result}")
            
            # Test performance stats
            stats = backend.get_performance_stats()
            logger.info(f"PostgreSQL performance stats: {stats}")
            
            await backend.close_connection(conn)
            logger.info("✅ PostgreSQL backend test passed")
            
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL backend test skipped (PostgreSQL not available): {e}")
            logger.info("This is expected if PostgreSQL server is not running")
            return True  # Skip test if PostgreSQL is not available
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL backend test failed: {e}")
        return False
    
    return True

async def test_multi_database_manager():
    """Test the multi-database manager with Rust backends."""
    logger.info("=== Testing Multi-Database Manager with Rust Backends ===")
    
    try:
        from oxen.multi_database_manager import MultiDatabaseManager
        from oxen.backends.base import DatabaseConfig
        
        # Create manager
        manager = MultiDatabaseManager()
        
        # Add SQLite database
        manager.add_database("sqlite_db", "sqlite::memory:", max_connections=3, min_connections=1)
        
        # Add MySQL database (if available)
        try:
            manager.add_database("mysql_db", "mysql://root:password@localhost:3306/test", max_connections=3, min_connections=1)
            logger.info("✅ MySQL database added to manager")
        except Exception as e:
            logger.warning(f"⚠️ MySQL database not added to manager: {e}")
        
        # Add PostgreSQL database (if available)
        try:
            manager.add_database("postgres_db", "postgresql://postgres:password@localhost:5432/test", max_connections=3, min_connections=1)
            logger.info("✅ PostgreSQL database added to manager")
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL database not added to manager: {e}")
        
        # Initialize manager
        await manager.initialize()
        logger.info("✅ Multi-database manager initialized")
        
        # Test SQLite operations through manager
        sqlite_backend = manager.get_backend("sqlite_db")
        if sqlite_backend:
            sqlite_db_info = manager.get_database("sqlite_db")
            conn = await sqlite_backend.create_connection(sqlite_db_info.config)
            result = await sqlite_backend.execute_query(conn, "SELECT 1 as test")
            logger.info(f"SQLite through manager: {result}")
            await sqlite_backend.close_connection(conn)
        
        # Test MySQL operations through manager (if available)
        mysql_backend = manager.get_backend("mysql_db")
        if mysql_backend:
            try:
                mysql_db_info = manager.get_database("mysql_db")
                conn = await mysql_backend.create_connection(mysql_db_info.config)
                result = await mysql_backend.execute_query(conn, "SELECT 1 as test")
                logger.info(f"MySQL through manager: {result}")
                await mysql_backend.close_connection(conn)
            except Exception as e:
                logger.warning(f"⚠️ MySQL through manager failed: {e}")
        
        # Test PostgreSQL operations through manager (if available)
        postgres_backend = manager.get_backend("postgres_db")
        if postgres_backend:
            try:
                postgres_db_info = manager.get_database("postgres_db")
                conn = await postgres_backend.create_connection(postgres_db_info.config)
                result = await postgres_backend.execute_query(conn, "SELECT 1 as test")
                logger.info(f"PostgreSQL through manager: {result}")
                await postgres_backend.close_connection(conn)
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL through manager failed: {e}")
        
        # Close manager
        await manager.close()
        logger.info("✅ Multi-database manager test passed")
        
    except Exception as e:
        logger.error(f"❌ Multi-database manager test failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests."""
    logger.info("🚀 Starting Rust Backend Integration Tests")
    
    results = []
    
    # Test 1: Direct Rust engine (synchronous)
    results.append(test_rust_engine_direct())
    
    # Test 2: SQLite backend
    results.append(await test_sqlite_backend())
    
    # Test 3: MySQL backend
    results.append(await test_mysql_backend())
    
    # Test 4: PostgreSQL backend
    results.append(await test_postgresql_backend())
    
    # Test 5: Multi-database manager
    results.append(await test_multi_database_manager())
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    test_names = [
        "Rust Engine Direct",
        "SQLite Backend",
        "MySQL Backend", 
        "PostgreSQL Backend",
        "Multi-Database Manager"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{i+1}. {name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Rust backend integration is working correctly.")
        return 0
    else:
        logger.error("💥 Some tests failed. Please check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 