#!/usr/bin/env python3
"""
Test Performance Benchmarks

This script runs the OxenORM performance benchmarks and validates the results.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from benchmarks.performance_test import PerformanceBenchmark, main


async def test_benchmark_system():
    """Test the benchmark system with a small dataset."""
    print("🧪 Testing OxenORM Performance Benchmark System")
    print("=" * 60)
    
    # Create benchmark instance
    benchmark = PerformanceBenchmark("sqlite:///test_benchmark.db")
    
    try:
        # Run benchmarks with small dataset for testing
        print("\n🔄 Running test benchmarks...")
        suite = await benchmark.run_benchmarks([10, 50])  # Small numbers for testing
        
        # Validate results
        print("\n📊 Validating benchmark results...")
        
        # Check if we have any results
        if not suite.results:
            print("❌ No benchmark results generated!")
            return False
        
        # Check if we have successful tests
        successful_tests = [r for r in suite.results if r.success]
        if not successful_tests:
            print("❌ No successful benchmark tests!")
            return False
        
        print(f"✅ Generated {len(suite.results)} benchmark results")
        print(f"✅ {len(successful_tests)} successful tests")
        
        # Print summary
        benchmark.print_summary(suite)
        
        # Save results
        filename = benchmark.save_results(suite, "test_benchmark_results.json")
        print(f"✅ Results saved to {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Benchmark test failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            await benchmark.cleanup_database()
            if os.path.exists("test_benchmark.db"):
                os.remove("test_benchmark.db")
        except:
            pass


async def test_monitoring_system():
    """Test the performance monitoring system."""
    print("\n🧪 Testing OxenORM Performance Monitoring System")
    print("=" * 60)
    
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
        print(f"❌ Monitoring test failed: {e}")
        return False


async def test_fastapi_integration():
    """Test the FastAPI integration."""
    print("\n🧪 Testing OxenORM FastAPI Integration")
    print("=" * 60)
    
    try:
        from oxen.contrib.fastapi import (
            OxenCRUDBase,
            create_pydantic_model_from_oxen_model,
            OxenAPIBuilder
        )
        
        # Test Pydantic model creation
        from oxen.models import Model
        from oxen.fields import CharField, IntField
        
        class TestModel(Model):
            name = CharField(max_length=100)
            value = IntField()
            
            class Meta:
                table_name = "test_model"
        
        # Create Pydantic model
        pydantic_model = create_pydantic_model_from_oxen_model(TestModel)
        print(f"✅ Pydantic model created: {pydantic_model.__name__}")
        
        # Test API builder
        api_builder = OxenAPIBuilder(title="Test API", version="1.0.0")
        print("✅ API builder created")
        
        # Test adding model
        api_builder.add_model(TestModel, prefix="/test", tags=["Test"])
        print("✅ Model added to API builder")
        
        # Build API
        app = api_builder.build()
        print(f"✅ FastAPI app built with {len(app.routes)} routes")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI integration test failed: {e}")
        return False


async def run_all_tests():
    """Run all performance and integration tests."""
    print("🚀 Running OxenORM Phase 1 Tests")
    print("=" * 60)
    
    tests = [
        ("Benchmark System", test_benchmark_system),
        ("Monitoring System", test_monitoring_system),
        ("FastAPI Integration", test_fastapi_integration),
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
        print("🎉 All tests passed! Phase 1 is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1) 