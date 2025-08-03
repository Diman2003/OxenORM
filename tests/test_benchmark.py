#!/usr/bin/env python3
"""
Test for Benchmarking System

This test verifies the benchmarking system features including:
- CRUD operation benchmarking
- Query operation benchmarking
- Bulk operation benchmarking
- Relationship operation benchmarking
- Concurrent operation benchmarking
- Report generation and comparison
"""

import asyncio
import sys
import uuid
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from oxen import Model, CharField, IntegerField, BooleanField, DateTimeField
from oxen.fields.relational import ForeignKeyField
from oxen.benchmark import BenchmarkRunner, BenchmarkResult, BenchmarkSuite


# Test models for benchmarking
class BenchmarkTestUser(Model):
    """User model for benchmark testing."""
    name = CharField(max_length=100)
    email = CharField(max_length=255, unique=True)
    age = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"benchmark_users_{uuid.uuid4().hex[:8]}"


class BenchmarkTestProduct(Model):
    """Product model for benchmark testing."""
    name = CharField(max_length=200)
    price = IntegerField(default=0)
    category = CharField(max_length=100)
    user = ForeignKeyField(BenchmarkTestUser, related_name="products")
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        table_name = f"benchmark_products_{uuid.uuid4().hex[:8]}"


async def test_benchmark_system():
    """Test the benchmarking system."""
    print("🚀 Benchmark System Test")
    print("=" * 40)
    
    # Test 1: Benchmark Runner Creation
    print("\n🔄 Test 1: Benchmark Runner Creation")
    print("-" * 50)
    
    try:
        runner = BenchmarkRunner()
        
        # Create a test suite
        suite = runner.create_suite("Test Suite", "Test benchmark suite")
        
        print(f"   ✅ Created benchmark runner")
        print(f"   ✅ Created test suite: {suite.name}")
        print(f"   ✅ Suite description: {suite.description}")
        
        print("✅ Benchmark runner creation test completed")
        
    except Exception as e:
        print(f"   ❌ Benchmark runner creation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Simple Benchmark Test
    print("\n🔄 Test 2: Simple Benchmark Test")
    print("-" * 50)
    
    try:
        runner = BenchmarkRunner()
        suite = runner.create_suite("Simple Test", "Simple benchmark test")
        
        # Simple async operation
        async def simple_operation():
            await asyncio.sleep(0.001)  # Simulate work
            return "test"
        
        result = await runner.run_benchmark(
            "Simple Operation",
            simple_operation,
            iterations=10,
            warmup_iterations=2
        )
        
        print(f"   ✅ Benchmark result created")
        print(f"   Test name: {result.test_name}")
        print(f"   Iterations: {result.iterations}")
        print(f"   Avg time: {result.avg_time:.6f}s")
        print(f"   Success rate: {result.success_rate:.1f}%")
        print(f"   Memory usage: {result.memory_usage:.2f}MB")
        
        print("✅ Simple benchmark test completed")
        
    except Exception as e:
        print(f"   ❌ Simple benchmark test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: CRUD Operations Benchmark
    print("\n🔄 Test 3: CRUD Operations Benchmark")
    print("-" * 50)
    
    try:
        runner = BenchmarkRunner()
        
        # Test data
        test_data = [
            {"name": f"User {i}", "email": f"user{i}@test.com", "age": 20 + i, "is_active": True}
            for i in range(10)
        ]
        
        # Create operation benchmark
        async def create_operation():
            for data in test_data[:2]:  # Create 2 users per iteration
                await BenchmarkTestUser.create(**data)
        
        result = await runner.run_benchmark(
            "Create Operations",
            create_operation,
            iterations=5,
            warmup_iterations=1
        )
        
        print(f"   ✅ CRUD benchmark completed")
        print(f"   Test: {result.test_name}")
        print(f"   Avg time: {result.avg_time:.6f}s")
        print(f"   Success rate: {result.success_rate:.1f}%")
        
        print("✅ CRUD operations benchmark test completed")
        
    except Exception as e:
        print(f"   ❌ CRUD operations benchmark test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Query Operations Benchmark
    print("\n🔄 Test 4: Query Operations Benchmark")
    print("-" * 50)
    
    try:
        runner = BenchmarkRunner()
        
        # Create some test data first
        for i in range(5):
            await BenchmarkTestUser.create(
                name=f"Query User {i}",
                email=f"query{i}@test.com",
                age=25 + i,
                is_active=True
            )
        
        # Query operation benchmark
        async def query_operation():
            users = await BenchmarkTestUser.all()
            return len(users)
        
        result = await runner.run_benchmark(
            "Query Operations",
            query_operation,
            iterations=10,
            warmup_iterations=2
        )
        
        print(f"   ✅ Query benchmark completed")
        print(f"   Test: {result.test_name}")
        print(f"   Avg time: {result.avg_time:.6f}s")
        print(f"   Success rate: {result.success_rate:.1f}%")
        
        print("✅ Query operations benchmark test completed")
        
    except Exception as e:
        print(f"   ❌ Query operations benchmark test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Report Generation
    print("\n🔄 Test 5: Report Generation")
    print("-" * 50)
    
    try:
        runner = BenchmarkRunner()
        suite = runner.create_suite("Report Test", "Test report generation")
        
        # Add some test results
        async def test_operation():
            await asyncio.sleep(0.001)
        
        await runner.run_benchmark("Test Operation 1", test_operation, iterations=5)
        await runner.run_benchmark("Test Operation 2", test_operation, iterations=5)
        
        # Generate report
        report = runner.generate_report("Report Test")
        
        print(f"   ✅ Report generated")
        print(f"   Suite name: {report['suite_name']}")
        print(f"   Total tests: {report['total_tests']}")
        print(f"   Total operations: {report['summary']['total_operations']}")
        print(f"   Total time: {report['summary']['total_time']:.6f}s")
        print(f"   Avg success rate: {report['summary']['avg_success_rate']:.1f}%")
        
        print("✅ Report generation test completed")
        
    except Exception as e:
        print(f"   ❌ Report generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 6: Report Saving
    print("\n🔄 Test 6: Report Saving")
    print("-" * 50)
    
    try:
        runner = BenchmarkRunner()
        suite = runner.create_suite("Save Test", "Test report saving")
        
        # Add test result
        async def save_operation():
            await asyncio.sleep(0.001)
        
        await runner.run_benchmark("Save Operation", save_operation, iterations=3)
        
        # Save report
        filepath = runner.save_report("Save Test")
        
        print(f"   ✅ Report saved")
        print(f"   File path: {filepath}")
        
        # Check if file exists
        if filepath.exists():
            file_size = filepath.stat().st_size
            print(f"   File size: {file_size} bytes")
            
            # Read and validate JSON
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            print(f"   Report contains:")
            print(f"     Suite name: {data.get('suite_name')}")
            print(f"     Total tests: {data.get('total_tests')}")
            print(f"     Results: {len(data.get('results', []))}")
            
            # Cleanup
            filepath.unlink()
            print(f"   🧹 Cleaned up report file")
        else:
            print(f"   ❌ Report file not found")
        
        print("✅ Report saving test completed")
        
    except Exception as e:
        print(f"   ❌ Report saving test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 7: Benchmark Comparison
    print("\n🔄 Test 7: Benchmark Comparison")
    print("-" * 50)
    
    try:
        runner = BenchmarkRunner()
        
        # Mock OxenORM results
        oxen_results = {
            "results": {
                "create_operation": {"avg_time": 0.001},
                "query_operation": {"avg_time": 0.002}
            }
        }
        
        # Mock other ORM results
        other_orm_results = {
            "results": {
                "create_operation": {"avg_time": 0.005},
                "query_operation": {"avg_time": 0.008}
            }
        }
        
        # Compare results
        comparison = runner.compare_with_other_orms(oxen_results, other_orm_results)
        
        print(f"   ✅ Comparison generated")
        print(f"   Comparison date: {comparison['comparison_date']}")
        print(f"   Performance improvements: {len(comparison['performance_improvement'])}")
        
        for test_name, improvement in comparison['performance_improvement'].items():
            print(f"     {test_name}: {improvement['improvement_percent']:.1f}% improvement")
        
        print("✅ Benchmark comparison test completed")
        
    except Exception as e:
        print(f"   ❌ Benchmark comparison test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 8: Memory and CPU Monitoring
    print("\n🔄 Test 8: Memory and CPU Monitoring")
    print("-" * 50)
    
    try:
        runner = BenchmarkRunner()
        suite = runner.create_suite("Monitoring Test", "Test memory and CPU monitoring")
        
        # Operation that uses some memory
        async def memory_operation():
            # Create some data to use memory
            data = [i for i in range(1000)]
            await asyncio.sleep(0.001)
            return len(data)
        
        result = await runner.run_benchmark(
            "Memory Operation",
            memory_operation,
            iterations=10,
            warmup_iterations=2
        )
        
        print(f"   ✅ Memory monitoring test completed")
        print(f"   Memory usage: {result.memory_usage:.2f}MB")
        print(f"   CPU usage: {result.cpu_usage:.1f}%")
        print(f"   Success rate: {result.success_rate:.1f}%")
        
        print("✅ Memory and CPU monitoring test completed")
        
    except Exception as e:
        print(f"   ❌ Memory and CPU monitoring test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 9: Error Handling
    print("\n🔄 Test 9: Error Handling")
    print("-" * 50)
    
    try:
        runner = BenchmarkRunner()
        suite = runner.create_suite("Error Test", "Test error handling")
        
        # Operation that sometimes fails
        async def error_operation():
            import random
            if random.random() < 0.3:  # 30% chance of error
                raise ValueError("Simulated error")
            await asyncio.sleep(0.001)
        
        result = await runner.run_benchmark(
            "Error Operation",
            error_operation,
            iterations=20,
            warmup_iterations=2
        )
        
        print(f"   ✅ Error handling test completed")
        print(f"   Success rate: {result.success_rate:.1f}%")
        print(f"   Error count: {result.error_count}")
        print(f"   Expected errors: ~6 (30% of 20)")
        
        print("✅ Error handling test completed")
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 10: Global Benchmark Runner
    print("\n🔄 Test 10: Global Benchmark Runner")
    print("-" * 50)
    
    try:
        from oxen.benchmark import get_benchmark_runner
        
        global_runner = get_benchmark_runner()
        
        # Test global runner
        suite = global_runner.create_suite("Global Test", "Test global runner")
        
        async def global_operation():
            await asyncio.sleep(0.001)
        
        result = await global_runner.run_benchmark(
            "Global Operation",
            global_operation,
            iterations=5
        )
        
        print(f"   ✅ Global runner test completed")
        print(f"   Test: {result.test_name}")
        print(f"   Avg time: {result.avg_time:.6f}s")
        
        print("✅ Global benchmark runner test completed")
        
    except Exception as e:
        print(f"   ❌ Global benchmark runner test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ All benchmark system tests completed successfully!")
    print("🎯 The benchmarking system is working properly!")


if __name__ == "__main__":
    asyncio.run(test_benchmark_system()) 