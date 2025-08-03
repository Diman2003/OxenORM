#!/usr/bin/env python3
"""
Benchmarking System for OxenORM

This module provides comprehensive benchmarking tools to test
OxenORM performance against other ORMs and provide detailed metrics.
"""

import asyncio
import time
import statistics
import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc


@dataclass
class BenchmarkResult:
    """Represents the result of a single benchmark test."""
    test_name: str
    operation: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    std_dev: float
    memory_usage: float
    cpu_usage: float
    success_rate: float
    error_count: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BenchmarkSuite:
    """Represents a complete benchmark suite."""
    name: str
    description: str
    results: List[BenchmarkResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class BenchmarkRunner:
    """Main benchmark runner for OxenORM performance testing."""
    
    def __init__(self):
        self.suites: Dict[str, BenchmarkSuite] = {}
        self.current_suite: Optional[BenchmarkSuite] = None
        self.results_dir = Path("benchmarks")
        self.results_dir.mkdir(exist_ok=True)
    
    def create_suite(self, name: str, description: str = "") -> BenchmarkSuite:
        """Create a new benchmark suite."""
        suite = BenchmarkSuite(name=name, description=description)
        self.suites[name] = suite
        self.current_suite = suite
        return suite
    
    async def run_benchmark(
        self,
        test_name: str,
        operation: Callable,
        iterations: int = 1000,
        warmup_iterations: int = 100,
        timeout: Optional[float] = None
    ) -> BenchmarkResult:
        """Run a single benchmark test."""
        print(f"🔄 Running benchmark: {test_name}")
        
        # Warmup phase
        if warmup_iterations > 0:
            print(f"   Warming up with {warmup_iterations} iterations...")
            for _ in range(warmup_iterations):
                try:
                    await operation()
                except Exception:
                    pass
        
        # Main benchmark phase
        times = []
        errors = 0
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        print(f"   Running {iterations} iterations...")
        
        for i in range(iterations):
            try:
                start_time = time.perf_counter()
                await operation()
                end_time = time.perf_counter()
                times.append(end_time - start_time)
                
                if i % 100 == 0:
                    print(f"     Progress: {i}/{iterations}")
                    
            except Exception as e:
                errors += 1
                print(f"     Error in iteration {i}: {e}")
        
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        end_cpu = psutil.cpu_percent()
        
        if not times:
            raise ValueError("No successful iterations completed")
        
        # Calculate statistics
        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        memory_usage = end_memory - start_memory
        cpu_usage = (start_cpu + end_cpu) / 2
        success_rate = (len(times) / iterations) * 100
        
        result = BenchmarkResult(
            test_name=test_name,
            operation=operation.__name__ if hasattr(operation, '__name__') else str(operation),
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            success_rate=success_rate,
            error_count=errors
        )
        
        if self.current_suite:
            self.current_suite.results.append(result)
        
        print(f"   ✅ Completed: {test_name}")
        print(f"      Avg time: {avg_time:.6f}s")
        print(f"      Success rate: {success_rate:.1f}%")
        print(f"      Memory usage: {memory_usage:.2f}MB")
        
        return result
    
    async def benchmark_crud_operations(self, model_class, test_data: List[Dict[str, Any]]):
        """Benchmark CRUD operations."""
        suite = self.create_suite("CRUD Operations", "Test Create, Read, Update, Delete operations")
        
        # Create operations
        async def create_operation():
            for data in test_data:
                await model_class.create(**data)
        
        await self.run_benchmark("Create Operations", create_operation, iterations=100)
        
        # Read operations
        async def read_operation():
            await model_class.all()
        
        await self.run_benchmark("Read Operations", read_operation, iterations=500)
        
        # Update operations
        async def update_operation():
            instances = await model_class.all()
            for instance in instances[:10]:  # Update first 10
                await instance.update(name=f"Updated {uuid.uuid4().hex[:8]}")
        
        await self.run_benchmark("Update Operations", update_operation, iterations=100)
        
        # Delete operations
        async def delete_operation():
            instances = await model_class.all()
            for instance in instances[:5]:  # Delete first 5
                await instance.delete()
        
        await self.run_benchmark("Delete Operations", delete_operation, iterations=50)
    
    async def benchmark_query_operations(self, model_class, test_data: List[Dict[str, Any]]):
        """Benchmark query operations."""
        suite = self.create_suite("Query Operations", "Test various query operations")
        
        # Create test data
        for data in test_data:
            await model_class.create(**data)
        
        # Simple filter
        async def simple_filter():
            await model_class.filter(name__icontains="test")
        
        await self.run_benchmark("Simple Filter", simple_filter, iterations=200)
        
        # Complex filter
        async def complex_filter():
            await model_class.filter(
                name__icontains="test",
                age__gte=18,
                is_active=True
            )
        
        await self.run_benchmark("Complex Filter", complex_filter, iterations=200)
        
        # Ordering
        async def ordering():
            await model_class.all().order_by("name")
        
        await self.run_benchmark("Ordering", ordering, iterations=200)
        
        # Aggregation
        async def aggregation():
            await model_class.all().count()
        
        await self.run_benchmark("Aggregation", aggregation, iterations=200)
    
    async def benchmark_bulk_operations(self, model_class, test_data: List[Dict[str, Any]]):
        """Benchmark bulk operations."""
        suite = self.create_suite("Bulk Operations", "Test bulk create, update, delete operations")
        
        # Bulk create
        async def bulk_create():
            await model_class.bulk_create(test_data)
        
        await self.run_benchmark("Bulk Create", bulk_create, iterations=50)
        
        # Bulk update
        async def bulk_update():
            instances = await model_class.all()
            update_data = [{"name": f"Bulk Updated {i}"} for i in range(len(instances))]
            await model_class.bulk_update(instances, update_data)
        
        await self.run_benchmark("Bulk Update", bulk_update, iterations=50)
    
    async def benchmark_relationship_operations(self, user_model, product_model, test_data: List[Dict[str, Any]]):
        """Benchmark relationship operations."""
        suite = self.create_suite("Relationship Operations", "Test relationship queries and operations")
        
        # Create test data with relationships
        users = []
        for i in range(10):
            user = await user_model.create(name=f"User {i}", email=f"user{i}@test.com")
            users.append(user)
        
        for user in users:
            for i in range(5):
                await product_model.create(
                    name=f"Product {i}",
                    price=100 + i,
                    user=user
                )
        
        # Relationship queries
        async def relationship_query():
            users_with_products = await user_model.all().prefetch_related("products")
            for user in users_with_products:
                products = user.products
                _ = len(products)
        
        await self.run_benchmark("Relationship Query", relationship_query, iterations=100)
        
        # Reverse relationship
        async def reverse_relationship():
            products = await product_model.all()
            for product in products:
                user = await product.user
                _ = user.name
        
        await self.run_benchmark("Reverse Relationship", reverse_relationship, iterations=100)
    
    async def benchmark_concurrent_operations(self, model_class, test_data: List[Dict[str, Any]]):
        """Benchmark concurrent operations."""
        suite = self.create_suite("Concurrent Operations", "Test concurrent database operations")
        
        async def concurrent_create():
            tasks = []
            for data in test_data:
                task = model_class.create(**data)
                tasks.append(task)
            await asyncio.gather(*tasks)
        
        await self.run_benchmark("Concurrent Create", concurrent_create, iterations=50)
        
        async def concurrent_read():
            tasks = []
            for _ in range(10):
                task = model_class.all()
                tasks.append(task)
            await asyncio.gather(*tasks)
        
        await self.run_benchmark("Concurrent Read", concurrent_read, iterations=100)
    
    def generate_report(self, suite_name: str) -> Dict[str, Any]:
        """Generate a comprehensive benchmark report."""
        if suite_name not in self.suites:
            raise ValueError(f"Suite '{suite_name}' not found")
        
        suite = self.suites[suite_name]
        
        report = {
            "suite_name": suite.name,
            "description": suite.description,
            "created_at": suite.created_at.isoformat(),
            "total_tests": len(suite.results),
            "summary": {
                "total_operations": sum(r.iterations for r in suite.results),
                "total_time": sum(r.total_time for r in suite.results),
                "avg_success_rate": statistics.mean([r.success_rate for r in suite.results]),
                "total_memory_usage": sum(r.memory_usage for r in suite.results),
                "avg_cpu_usage": statistics.mean([r.cpu_usage for r in suite.results])
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "operation": r.operation,
                    "iterations": r.iterations,
                    "total_time": r.total_time,
                    "avg_time": r.avg_time,
                    "min_time": r.min_time,
                    "max_time": r.max_time,
                    "median_time": r.median_time,
                    "std_dev": r.std_dev,
                    "memory_usage": r.memory_usage,
                    "cpu_usage": r.cpu_usage,
                    "success_rate": r.success_rate,
                    "error_count": r.error_count,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in suite.results
            ]
        }
        
        return report
    
    def save_report(self, suite_name: str, filename: Optional[str] = None):
        """Save benchmark report to file."""
        report = self.generate_report(suite_name)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_report_{suite_name}_{timestamp}.json"
        
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Benchmark report saved to: {filepath}")
        return filepath
    
    def compare_with_other_orms(self, oxen_results: Dict[str, Any], other_orm_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare OxenORM results with other ORMs."""
        comparison = {
            "oxenorm_results": oxen_results,
            "other_orm_results": other_orm_results,
            "performance_improvement": {},
            "comparison_date": datetime.now().isoformat()
        }
        
        # Calculate performance improvements
        for result in oxen_results.get("results", []):
            if isinstance(result, dict):
                test_name = result.get("test_name", "")
                oxen_avg = result.get("avg_time", 0)
                other_avg = other_orm_results.get("results", {}).get(test_name, {}).get("avg_time", 0)
                
                if other_avg > 0:
                    improvement = ((other_avg - oxen_avg) / other_avg) * 100
                    comparison["performance_improvement"][test_name] = {
                        "improvement_percent": improvement,
                        "oxen_time": oxen_avg,
                        "other_time": other_avg
                    }
        
        return comparison


# Global benchmark runner instance
_global_runner = BenchmarkRunner()


def get_benchmark_runner() -> BenchmarkRunner:
    """Get the global benchmark runner instance."""
    return _global_runner


async def run_comprehensive_benchmark():
    """Run a comprehensive benchmark suite."""
    from oxen import Model, CharField, IntegerField, BooleanField, DateTimeField
    from oxen.fields.relational import ForeignKeyField
    
    # Define test models
    class BenchmarkUser(Model):
        name = CharField(max_length=100)
        email = CharField(max_length=255, unique=True)
        age = IntegerField(default=0)
        is_active = BooleanField(default=True)
        created_at = DateTimeField(auto_now_add=True)
        
        class Meta:
            table_name = f"benchmark_users_{uuid.uuid4().hex[:8]}"
    
    class BenchmarkProduct(Model):
        name = CharField(max_length=200)
        price = IntegerField(default=0)
        category = CharField(max_length=100)
        user = ForeignKeyField(BenchmarkUser, related_name="products")
        created_at = DateTimeField(auto_now_add=True)
        
        class Meta:
            table_name = f"benchmark_products_{uuid.uuid4().hex[:8]}"
    
    # Test data
    test_users = [
        {"name": f"User {i}", "email": f"user{i}@test.com", "age": 20 + i, "is_active": True}
        for i in range(100)
    ]
    
    test_products = [
        {"name": f"Product {i}", "price": 100 + i, "category": "Electronics"}
        for i in range(50)
    ]
    
    runner = get_benchmark_runner()
    
    print("🚀 Starting Comprehensive OxenORM Benchmark")
    print("=" * 50)
    
    # Run different benchmark suites
    await runner.benchmark_crud_operations(BenchmarkUser, test_users)
    await runner.benchmark_query_operations(BenchmarkUser, test_users)
    await runner.benchmark_bulk_operations(BenchmarkUser, test_users)
    await runner.benchmark_relationship_operations(BenchmarkUser, BenchmarkProduct, test_products)
    await runner.benchmark_concurrent_operations(BenchmarkUser, test_users)
    
    # Generate and save reports
    for suite_name in runner.suites:
        runner.save_report(suite_name)
    
    print("\n✅ Comprehensive benchmark completed!")
    print("📊 Check the 'benchmarks' directory for detailed reports")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_benchmark()) 