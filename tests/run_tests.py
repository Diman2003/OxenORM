#!/usr/bin/env python3
"""
Test Runner for OxenORM
Run all tests or specific test files
"""

import sys
import os
import asyncio
import importlib.util
from pathlib import Path

# Add the parent directory to the path so we can import oxen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_file(test_file: str) -> bool:
    """Run a specific test file."""
    try:
        print(f"🚀 Running test: {test_file}")
        print("=" * 50)
        
        # Import and run the test
        spec = importlib.util.spec_from_file_location("test_module", test_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run the main function if it exists
        if hasattr(module, 'main'):
            asyncio.run(module.main())
            print(f"✅ {test_file} completed successfully")
            return True
        else:
            print(f"⚠️  {test_file} has no main() function")
            return False
            
    except Exception as e:
        print(f"❌ {test_file} failed: {str(e)}")
        return False

def run_all_tests():
    """Run all test files in the tests directory."""
    tests_dir = Path(__file__).parent
    test_files = list(tests_dir.glob("test_*.py"))
    
    print(f"🚀 Running {len(test_files)} tests...")
    print("=" * 50)
    
    results = {}
    for test_file in test_files:
        if test_file.name != "run_tests.py":  # Skip this file
            success = run_test_file(str(test_file))
            results[test_file.name] = success
            print()
    
    # Print summary
    print("=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:40} {status}")
    
    print("=" * 50)
    print(f"📈 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        if not test_file.endswith('.py'):
            test_file += '.py'
        
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            run_test_file(str(test_path))
        else:
            print(f"❌ Test file not found: {test_file}")
    else:
        # Run all tests
        run_all_tests()

if __name__ == "__main__":
    main() 