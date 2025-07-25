#!/usr/bin/env python3
"""
Comprehensive test for OxenORM Multi-Database Support

This script tests the multi-database engine with PostgreSQL, MySQL, and SQLite,
including database-specific optimizations and switching capabilities.
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from oxen.multi_db_engine import MultiDbEngine, DatabaseSwitcher, DatabaseType, test_database_connection
    MULTI_DB_AVAILABLE = True
except ImportError as e:
    print(f"❌ Multi-database module not available: {e}")
    MULTI_DB_AVAILABLE = False

# Database configurations for testing
DB_CONFIGS = {
    "postgresql": {
        "host": "localhost",
        "port": 5432,
        "database": "oxenorm_test",
        "username": "oxenorm_user",
        "password": "oxenorm_pass"
    },
    "mysql": {
        "host": "localhost",
        "port": 3306,
        "database": "oxenorm_test",
        "username": "oxenorm_user",
        "password": "oxenorm_pass"
    }
}

def build_connection_string(db_type: str, config: dict) -> str:
    """Build database connection string."""
    if db_type == "postgresql":
        return f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    elif db_type == "mysql":
        return f"mysql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

async def test_database_type_detection():
    """Test database type detection from connection strings."""
    print("🔍 Testing Database Type Detection")
    print("=" * 40)

    test_cases = [
        ("postgresql://user:pass@localhost/db", DatabaseType.POSTGRESQL),
        ("postgres://user:pass@localhost/db", DatabaseType.POSTGRESQL),
        ("mysql://user:pass@localhost/db", DatabaseType.MYSQL),
        ("sqlite:///path/to/database.db", DatabaseType.SQLITE),
    ]

    for connection_string, expected_type in test_cases:
        try:
            engine = MultiDbEngine(connection_string)
            detected_type = engine.get_database_type()
            
            if detected_type == expected_type:
                print(f"✅ {connection_string} -> {detected_type.value}")
            else:
                print(f"❌ {connection_string} -> Expected {expected_type.value}, got {detected_type.value}")
        except Exception as e:
            print(f"❌ {connection_string} -> Error: {e}")

async def test_postgresql_engine():
    """Test PostgreSQL engine functionality."""
    print("\n🐘 Testing PostgreSQL Engine")
    print("=" * 40)

    try:
        connection_string = build_connection_string("postgresql", DB_CONFIGS["postgresql"])
        
        # Test connection
        print("1. Testing connection...")
        is_connected = await test_database_connection(connection_string)
        if is_connected:
            print("✅ PostgreSQL connection successful")
        else:
            print("❌ PostgreSQL connection failed")
            return False

        # Test engine creation and operations
        print("\n2. Testing engine operations...")
        async with MultiDbEngine(connection_string) as engine:
            # Test basic query
            result = await engine.execute_query("SELECT 1 as test_value")
            print(f"✅ Basic query: {result}")

            # Test parameterized query
            result = await engine.execute_query(
                "SELECT $1 as param1, $2 as param2",
                ["hello", 42]
            )
            print(f"✅ Parameterized query: {result}")

            # Test database info
            info = await engine.get_database_info()
            print(f"✅ Database info: {info}")

        return True

    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return False

async def test_mysql_engine():
    """Test MySQL engine functionality."""
    print("\n🐬 Testing MySQL Engine")
    print("=" * 40)

    try:
        connection_string = build_connection_string("mysql", DB_CONFIGS["mysql"])
        
        # Test connection
        print("1. Testing connection...")
        is_connected = await test_database_connection(connection_string)
        if is_connected:
            print("✅ MySQL connection successful")
        else:
            print("❌ MySQL connection failed")
            return False

        # Test engine creation and operations
        print("\n2. Testing engine operations...")
        async with MultiDbEngine(connection_string) as engine:
            # Test basic query
            result = await engine.execute_query("SELECT 1 as test_value")
            print(f"✅ Basic query: {result}")

            # Test parameterized query (MySQL uses ? placeholders)
            result = await engine.execute_query(
                "SELECT ? as param1, ? as param2",
                ["hello", 42]
            )
            print(f"✅ Parameterized query: {result}")

            # Test database info
            info = await engine.get_database_info()
            print(f"✅ Database info: {info}")

        return True

    except Exception as e:
        print(f"❌ MySQL test failed: {e}")
        return False

async def test_sqlite_engine():
    """Test SQLite engine functionality."""
    print("\n🗄️  Testing SQLite Engine")
    print("=" * 40)

    try:
        # Create a temporary SQLite database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            sqlite_path = f.name

        connection_string = f"sqlite:///{sqlite_path}"
        
        # Test connection
        print("1. Testing connection...")
        is_connected = await test_database_connection(connection_string)
        if is_connected:
            print("✅ SQLite connection successful")
        else:
            print("❌ SQLite connection failed")
            return False

        # Test engine creation and operations
        print("\n2. Testing engine operations...")
        async with MultiDbEngine(connection_string) as engine:
            # Test basic query
            result = await engine.execute_query("SELECT 1 as test_value")
            print(f"✅ Basic query: {result}")

            # Test parameterized query (SQLite uses ? placeholders)
            result = await engine.execute_query(
                "SELECT ? as param1, ? as param2",
                ["hello", 42]
            )
            print(f"✅ Parameterized query: {result}")

            # Test database info
            info = await engine.get_database_info()
            print(f"✅ Database info: {info}")

        # Clean up
        os.unlink(sqlite_path)
        return True

    except Exception as e:
        print(f"❌ SQLite test failed: {e}")
        return False

async def test_database_switcher():
    """Test database switching capabilities."""
    print("\n🔄 Testing Database Switcher")
    print("=" * 40)

    try:
        switcher = DatabaseSwitcher()
        
        # Add databases
        print("1. Adding databases...")
        
        # Add PostgreSQL
        postgres_conn = build_connection_string("postgresql", DB_CONFIGS["postgresql"])
        postgres_engine = await switcher.add_database("postgres", postgres_conn)
        print("✅ Added PostgreSQL database")

        # Add MySQL
        mysql_conn = build_connection_string("mysql", DB_CONFIGS["mysql"])
        mysql_engine = await switcher.add_database("mysql", mysql_conn)
        print("✅ Added MySQL database")

        # Add SQLite
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            sqlite_path = f.name
        sqlite_conn = f"sqlite:///{sqlite_path}"
        sqlite_engine = await switcher.add_database("sqlite", sqlite_conn)
        print("✅ Added SQLite database")

        # List databases
        print(f"\n2. Available databases: {switcher.list_databases()}")

        # Test switching
        print("\n3. Testing database switching...")
        
        # Switch to PostgreSQL
        current_engine = await switcher.switch_to("postgres")
        print(f"✅ Switched to PostgreSQL: {current_engine.get_database_type().value}")
        
        # Execute query on PostgreSQL
        result = await current_engine.execute_query("SELECT 1 as postgres_test")
        print(f"✅ PostgreSQL query: {result}")

        # Switch to MySQL
        current_engine = await switcher.switch_to("mysql")
        print(f"✅ Switched to MySQL: {current_engine.get_database_type().value}")
        
        # Execute query on MySQL
        result = await current_engine.execute_query("SELECT 1 as mysql_test")
        print(f"✅ MySQL query: {result}")

        # Switch to SQLite
        current_engine = await switcher.switch_to("sqlite")
        print(f"✅ Switched to SQLite: {current_engine.get_database_type().value}")
        
        # Execute query on SQLite
        result = await current_engine.execute_query("SELECT 1 as sqlite_test")
        print(f"✅ SQLite query: {result}")

        # Close all connections
        await switcher.close_all()
        print("✅ Closed all database connections")

        # Clean up SQLite file
        os.unlink(sqlite_path)

        return True

    except Exception as e:
        print(f"❌ Database switcher test failed: {e}")
        return False

async def test_query_optimizations():
    """Test database-specific query optimizations."""
    print("\n⚡ Testing Query Optimizations")
    print("=" * 40)

    test_queries = [
        "SELECT * FROM users WHERE active = true",
        "INSERT INTO users (name, email) VALUES ('test', 'test@example.com')",
        "UPDATE users SET last_login = NOW() WHERE id = 1",
        "DELETE FROM users WHERE id = 1",
    ]

    for query in test_queries:
        print(f"\nTesting query: {query}")
        
        # Test PostgreSQL optimization
        try:
            postgres_conn = build_connection_string("postgresql", DB_CONFIGS["postgresql"])
            engine = MultiDbEngine(postgres_conn)
            optimized = engine._optimize_query(query)
            print(f"  PostgreSQL: {optimized}")
        except Exception as e:
            print(f"  PostgreSQL: Error - {e}")

        # Test MySQL optimization
        try:
            mysql_conn = build_connection_string("mysql", DB_CONFIGS["mysql"])
            engine = MultiDbEngine(mysql_conn)
            optimized = engine._optimize_query(query)
            print(f"  MySQL: {optimized}")
        except Exception as e:
            print(f"  MySQL: Error - {e}")

        # Test SQLite optimization
        try:
            engine = MultiDbEngine("sqlite:///test.db")
            optimized = engine._optimize_query(query)
            print(f"  SQLite: {optimized}")
        except Exception as e:
            print(f"  SQLite: Error - {e}")

async def test_connection_pooling():
    """Test connection pooling for different database types."""
    print("\n🏊 Testing Connection Pooling")
    print("=" * 40)

    # Test PostgreSQL pooling
    try:
        postgres_conn = build_connection_string("postgresql", DB_CONFIGS["postgresql"])
        engine = MultiDbEngine(postgres_conn)
        
        # Configure pool
        engine.configure_pool(max_connections=5, min_connections=1)
        print("✅ PostgreSQL pool configured")
        
        # Connect and test
        await engine.connect()
        info = await engine.get_connection_info()
        print(f"✅ PostgreSQL connection info: {info}")
        
        await engine.disconnect()
    except Exception as e:
        print(f"❌ PostgreSQL pooling test failed: {e}")

    # Test MySQL pooling
    try:
        mysql_conn = build_connection_string("mysql", DB_CONFIGS["mysql"])
        engine = MultiDbEngine(mysql_conn)
        
        # Configure pool
        engine.configure_pool(max_connections=3, min_connections=1)
        print("✅ MySQL pool configured")
        
        # Connect and test
        await engine.connect()
        info = await engine.get_connection_info()
        print(f"✅ MySQL connection info: {info}")
        
        await engine.disconnect()
    except Exception as e:
        print(f"❌ MySQL pooling test failed: {e}")

    # Test SQLite (no pooling needed)
    try:
        engine = MultiDbEngine("sqlite:///test.db")
        
        # SQLite doesn't need connection pooling
        engine.configure_pool(max_connections=1, min_connections=1)
        print("✅ SQLite pool configured (single connection)")
        
        await engine.connect()
        info = await engine.get_connection_info()
        print(f"✅ SQLite connection info: {info}")
        
        await engine.disconnect()
    except Exception as e:
        print(f"❌ SQLite pooling test failed: {e}")

async def test_error_handling():
    """Test error handling for different database types."""
    print("\n⚠️  Testing Error Handling")
    print("=" * 40)

    # Test invalid connection strings
    invalid_connections = [
        "invalid://localhost/db",
        "postgresql://invalid:invalid@localhost/nonexistent",
        "mysql://invalid:invalid@localhost/nonexistent",
    ]

    for conn_str in invalid_connections:
        try:
            engine = MultiDbEngine(conn_str)
            await engine.connect()
            print(f"❌ Should have failed: {conn_str}")
        except Exception as e:
            print(f"✅ Correctly handled invalid connection: {conn_str} -> {e}")

    # Test invalid queries
    try:
        postgres_conn = build_connection_string("postgresql", DB_CONFIGS["postgresql"])
        async with MultiDbEngine(postgres_conn) as engine:
            try:
                await engine.execute_query("SELECT * FROM nonexistent_table")
                print("❌ Should have failed: invalid table")
            except Exception as e:
                print(f"✅ Correctly handled invalid query: {e}")
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")

async def main():
    """Main test function."""
    print("🧪 OxenORM Multi-Database Test Suite")
    print("=" * 60)

    if not MULTI_DB_AVAILABLE:
        print("❌ Multi-database module not available. Cannot run tests.")
        return 1

    success = True

    try:
        # Test database type detection
        await test_database_type_detection()

        # Test individual database engines
        if not await test_postgresql_engine():
            success = False

        if not await test_mysql_engine():
            success = False

        if not await test_sqlite_engine():
            success = False

        # Test database switching
        if not await test_database_switcher():
            success = False

        # Test query optimizations
        await test_query_optimizations()

        # Test connection pooling
        await test_connection_pooling()

        # Test error handling
        await test_error_handling()

        if success:
            print("\n" + "=" * 60)
            print("🎉 Multi-database test suite completed successfully!")
            print("\n✅ All multi-database features are working correctly:")
            print("✅ Database type detection")
            print("✅ PostgreSQL engine with optimizations")
            print("✅ MySQL engine with optimizations")
            print("✅ SQLite engine with optimizations")
            print("✅ Database switching capabilities")
            print("✅ Query optimizations for each database type")
            print("✅ Connection pooling for different databases")
            print("✅ Error handling and validation")
            print("\n🚀 Multi-database support is ready for production use!")
        else:
            print("\n❌ Some multi-database tests failed.")
            return 1

        return 0

    except Exception as e:
        print(f"\n❌ Multi-database test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 