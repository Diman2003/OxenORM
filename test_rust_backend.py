#!/usr/bin/env python3
"""
Test script for the enhanced OxenORM Rust backend.
This script tests the basic functionality of the Rust engine.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from oxen.rust_engine import OxenEngine
    RUST_AVAILABLE = True
except ImportError as e:
    print(f"❌ Rust engine not available: {e}")
    print("Please build the Rust extension first with: maturin develop")
    RUST_AVAILABLE = False

async def test_rust_backend():
    """Test the enhanced Rust backend functionality."""
    if not RUST_AVAILABLE:
        return False
    
    print("🚀 Testing Enhanced OxenORM Rust Backend")
    print("=" * 50)
    
    # Test 1: Create engine instance
    print("\n1. Creating engine instance...")
    try:
        engine = OxenEngine("postgresql://test:test@localhost:5432/test_db")
        print("✅ Engine created successfully")
    except Exception as e:
        print(f"❌ Failed to create engine: {e}")
        return False
    
    # Test 2: Configure pool settings
    print("\n2. Configuring pool settings...")
    try:
        engine.configure_pool(max_connections=5, min_connections=1)
        print("✅ Pool configured successfully")
    except Exception as e:
        print(f"❌ Failed to configure pool: {e}")
        return False
    
    # Test 3: Check connection status before connecting
    print("\n3. Checking connection status...")
    try:
        is_connected = engine.is_connected()
        print(f"✅ Connection status: {is_connected}")
        assert not is_connected, "Should not be connected initially"
    except Exception as e:
        print(f"❌ Failed to check connection status: {e}")
        return False
    
    # Test 4: Try to connect (this will fail without a real database, but should handle errors gracefully)
    print("\n4. Attempting to connect...")
    try:
        result = await engine.connect()
        print(f"✅ Connection result: {result}")
    except Exception as e:
        print(f"⚠️  Connection failed (expected without real DB): {e}")
        # This is expected without a real PostgreSQL database
    
    # Test 5: Test error handling for operations without connection
    print("\n5. Testing error handling...")
    try:
        result = await engine.execute_query("SELECT 1")
        print(f"❌ Should have failed: {result}")
        return False
    except Exception as e:
        print(f"✅ Correctly failed with: {e}")
    
    # Test 6: Test pool status (should fail without connection)
    print("\n6. Testing pool status...")
    try:
        status = await engine.get_pool_status()
        print(f"❌ Should have failed: {status}")
        return False
    except Exception as e:
        print(f"✅ Correctly failed with: {e}")
    
    # Test 7: Test transaction creation (should fail without connection)
    print("\n7. Testing transaction creation...")
    try:
        tx = await engine.begin_transaction()
        print(f"❌ Should have failed: {tx}")
        return False
    except Exception as e:
        print(f"✅ Correctly failed with: {e}")
    
    # Test 8: Test close
    print("\n8. Testing close...")
    try:
        result = await engine.close()
        print(f"✅ Close result: {result}")
    except Exception as e:
        print(f"❌ Failed to close: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    print("The Rust backend is working correctly with proper error handling.")
    return True

async def test_with_mock_connection():
    """Test with a mock connection string to verify parameter handling."""
    print("\n🔧 Testing with mock connection...")
    
    try:
        engine = OxenEngine("postgresql://user:pass@localhost:5432/db")
        
        # Test configuration
        engine.configure_pool(max_connections=10, min_connections=2)
        
        # Test connection status
        assert not engine.is_connected()
        
        print("✅ Mock connection tests passed")
        return True
    except Exception as e:
        print(f"❌ Mock connection tests failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🧪 OxenORM Rust Backend Test Suite")
    print("=" * 50)
    
    success = True
    
    # Test basic functionality
    if not await test_rust_backend():
        success = False
    
    # Test mock connection
    if not await test_with_mock_connection():
        success = False
    
    if success:
        print("\n🎉 All tests passed! The Rust backend is ready for real database integration.")
        print("\nNext steps:")
        print("1. Set up a PostgreSQL database")
        print("2. Update the connection string in the test")
        print("3. Run real database operations")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 