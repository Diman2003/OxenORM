#!/usr/bin/env python3
"""
Integration test for OxenORM Python-Rust bridge
"""

import asyncio
import sys
import os

# Add the current directory to the path so we can import oxen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from oxen import OxenEngine
    print("✓ Successfully imported OxenEngine from oxen package")
except ImportError as e:
    print(f"✗ Failed to import OxenEngine: {e}")
    sys.exit(1)

async def test_rust_bridge():
    """Test the Python-Rust bridge functionality"""
    print("\nTesting Python-Rust Bridge")
    print("=" * 40)
    
    try:
        # Test creating an engine instance
        engine = OxenEngine("sqlite:test.db")
        print("✓ Successfully created OxenEngine instance")
        
        # Test connecting to database
        await engine.connect()
        print("✓ Successfully connected to database")
        
        # Test disconnecting
        await engine.disconnect()
        print("✓ Successfully disconnected from database")
        
        print("\n🎉 Python-Rust bridge is working correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Bridge test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("OxenORM Integration Test")
    print("=" * 50)
    
    success = await test_rust_bridge()
    
    if success:
        print("\n✅ All integration tests passed!")
        print("\nNext steps:")
        print("1. Implement actual database operations in Rust")
        print("2. Add comprehensive integration tests")
        print("3. Run performance benchmarks")
        print("4. Add migration system")
    else:
        print("\n❌ Integration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 