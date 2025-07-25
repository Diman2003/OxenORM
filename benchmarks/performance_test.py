#!/usr/bin/env python3
"""
OxenORM Performance Benchmark Suite

This module provides comprehensive performance benchmarks comparing OxenORM against:
- Django ORM
- SQLAlchemy
- Tortoise ORM
- Raw SQL (baseline)

Benchmarks cover:
- CRUD operations (Create, Read, Update, Delete)
- Bulk operations
- Complex queries with joins
- Aggregation and grouping
- Connection pooling
- Memory usage
"""

import asyncio
import time
import psutil
import statistics
from typing import Dict, List, Any, Callable, Tuple
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path

# Benchmark imports
try:
    import django
    from django.db import connection
    from django.conf import settings
    from django.apps import apps
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

try:
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import declarative_base, sessionmaker
    from sqlalchemy import Column, Integer, String, DateTime, Text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

try:
    from tortoise import Tortoise, fields
    from tortoise.models import Model as TortoiseModel
    TORTOISE_AVAILABLE = True
except ImportError:
    TORTOISE_AVAILABLE = False

try:
    from oxen.models import Model
    from oxen.fields import IntField, CharField, DateTimeField, TextField
    from oxen.multi_db_engine import MultiDbEngine
    OXENORM_AVAILABLE = True
except ImportError:
    OXENORM_AVAILABLE = False


@dataclass
class BenchmarkResult:
    """Result of a single benchmark test."""
    operation: str
    framework: str
    duration_ms: float
    memory_mb: float
    records_processed: int
    success: bool
    error_message: str = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkSuite:
    """Complete benchmark suite results."""
    name: str
    results: List[BenchmarkResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def add_result(self, result: BenchmarkResult):
        """Add a benchmark result."""
        self.results.append(result)
    
    def get_framework_results(self, framework: str) -> List[BenchmarkResult]:
        """Get all results for a specific framework."""
        return [r for r in self.results if r.framework == framework]
    
    def calculate_summary(self):
        """Calculate summary statistics."""
        frameworks = set(r.framework for r in self.results)
        operations = set(r.operation for r in self.results)
        
        summary = {
            'total_tests': len(self.results),
            'frameworks': list(frameworks),
            'operations': list(operations),
            'framework_stats': {},
            'operation_stats': {},
            'performance_ranking': []
        }
        
        # Calculate framework statistics
        for framework in frameworks:
            framework_results = self.get_framework_results(framework)
            successful_results = [r for r in framework_results if r.success]
            
            if successful_results:
                avg_duration = statistics.mean(r.duration_ms for r in successful_results)
                avg_memory = statistics.mean(r.memory_mb for r in successful_results)
                total_records = sum(r.records_processed for r in successful_results)
                
                summary['framework_stats'][framework] = {
                    'total_tests': len(framework_results),
                    'successful_tests': len(successful_results),
                    'success_rate': len(successful_results) / len(framework_results),
                    'avg_duration_ms': avg_duration,
                    'avg_memory_mb': avg_memory,
                    'total_records_processed': total_records,
                    'operations_per_second': total_records / (avg_duration / 1000) if avg_duration > 0 else 0
                }
        
        # Calculate performance ranking
        framework_avg_durations = {
            fw: stats['avg_duration_ms'] 
            for fw, stats in summary['framework_stats'].items()
        }
        
        summary['performance_ranking'] = sorted(
            framework_avg_durations.items(),
            key=lambda x: x[1]
        )
        
        self.summary = summary
        return summary


class PerformanceBenchmark:
    """Main performance benchmarking class."""
    
    def __init__(self, database_url: str = "sqlite:///benchmark.db"):
        self.database_url = database_url
        self.results: List[BenchmarkResult] = []
        self.setup_models()
    
    def setup_models(self):
        """Setup models for each framework."""
        # OxenORM Models
        if OXENORM_AVAILABLE:
            class OxenUser(Model):
                username = CharField(max_length=100, unique=True)
                email = CharField(max_length=255, unique=True)
                bio = TextField(null=True)
                created_at = DateTimeField(auto_now_add=True)
                
                class Meta:
                    table_name = "oxen_users"
            
            class OxenPost(Model):
                title = CharField(max_length=200)
                content = TextField()
                author_id = IntField()
                created_at = DateTimeField(auto_now_add=True)
                
                class Meta:
                    table_name = "oxen_posts"
            
            self.oxen_models = {'User': OxenUser, 'Post': OxenPost}
        
        # Tortoise Models
        if TORTOISE_AVAILABLE:
            class TortoiseUser(TortoiseModel):
                id = fields.IntField(pk=True)
                username = fields.CharField(max_length=100, unique=True)
                email = fields.CharField(max_length=255, unique=True)
                bio = fields.TextField(null=True)
                created_at = fields.DatetimeField(auto_now_add=True)
                
                class Meta:
                    table = "tortoise_users"
            
            class TortoisePost(TortoiseModel):
                id = fields.IntField(pk=True)
                title = fields.CharField(max_length=200)
                content = fields.TextField()
                author = fields.ForeignKeyField('models.TortoiseUser', related_name='posts')
                created_at = fields.DatetimeField(auto_now_add=True)
                
                class Meta:
                    table = "tortoise_posts"
            
            self.tortoise_models = {'User': TortoiseUser, 'Post': TortoisePost}
        
        # SQLAlchemy Models
        if SQLALCHEMY_AVAILABLE:
            Base = declarative_base()
            
            class SQLAlchemyUser(Base):
                __tablename__ = 'sqlalchemy_users'
                
                id = Column(Integer, primary_key=True)
                username = Column(String(100), unique=True)
                email = Column(String(255), unique=True)
                bio = Column(Text, nullable=True)
                created_at = Column(DateTime)
            
            class SQLAlchemyPost(Base):
                __tablename__ = 'sqlalchemy_posts'
                
                id = Column(Integer, primary_key=True)
                title = Column(String(200))
                content = Column(Text)
                author_id = Column(Integer)
                created_at = Column(DateTime)
            
            self.sqlalchemy_models = {'User': SQLAlchemyUser, 'Post': SQLAlchemyPost}
    
    async def setup_database(self):
        """Setup database for benchmarking."""
        if OXENORM_AVAILABLE:
            # Setup OxenORM
            self.oxen_engine = MultiDbEngine(self.database_url)
            await self.oxen_engine.connect()
            
            # Create tables
            for model_class in self.oxen_models.values():
                await model_class._meta.create_table(self.oxen_engine)
        
        if TORTOISE_AVAILABLE:
            # Setup Tortoise
            await Tortoise.init(
                db_url=self.database_url,
                modules={'models': ['__main__']}
            )
            await Tortoise.generate_schemas()
        
        if SQLALCHEMY_AVAILABLE:
            # Setup SQLAlchemy
            self.sqlalchemy_engine = create_async_engine(self.database_url)
            async with self.sqlalchemy_engine.begin() as conn:
                for model_class in self.sqlalchemy_models.values():
                    await conn.run_sync(model_class.__table__.create)
    
    async def cleanup_database(self):
        """Cleanup database after benchmarking."""
        if OXENORM_AVAILABLE:
            await self.oxen_engine.disconnect()
        
        if TORTOISE_AVAILABLE:
            await Tortoise.close_connections()
        
        if SQLALCHEMY_AVAILABLE:
            await self.sqlalchemy_engine.dispose()
    
    def measure_memory(self) -> float:
        """Measure current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # Convert to MB
    
    async def benchmark_operation(
        self,
        operation_name: str,
        framework: str,
        operation_func: Callable,
        records_count: int = 1000
    ) -> BenchmarkResult:
        """Run a single benchmark operation."""
        start_memory = self.measure_memory()
        start_time = time.time()
        
        try:
            result = await operation_func(records_count)
            success = True
            error_message = None
        except Exception as e:
            result = None
            success = False
            error_message = str(e)
        
        end_time = time.time()
        end_memory = self.measure_memory()
        
        duration_ms = (end_time - start_time) * 1000
        memory_mb = end_memory - start_memory
        
        return BenchmarkResult(
            operation=operation_name,
            framework=framework,
            duration_ms=duration_ms,
            memory_mb=memory_mb,
            records_processed=records_count if success else 0,
            success=success,
            error_message=error_message
        )
    
    # OxenORM Benchmarks
    async def oxenorm_create_users(self, count: int):
        """Benchmark OxenORM user creation."""
        users = []
        for i in range(count):
            user = self.oxen_models['User'](
                username=f"user_{i}",
                email=f"user_{i}@example.com",
                bio=f"Bio for user {i}"
            )
            users.append(user)
        
        await self.oxen_models['User'].bulk_create(users)
        return count
    
    async def oxenorm_read_users(self, count: int):
        """Benchmark OxenORM user reading."""
        users = await self.oxen_models['User'].all().limit(count)
        return len(users)
    
    async def oxenorm_update_users(self, count: int):
        """Benchmark OxenORM user updating."""
        users = await self.oxen_models['User'].all().limit(count)
        for user in users:
            user.bio = f"Updated bio for {user.username}"
        
        await self.oxen_models['User'].bulk_update(users, ['bio'])
        return len(users)
    
    async def oxenorm_delete_users(self, count: int):
        """Benchmark OxenORM user deletion."""
        users = await self.oxen_models['User'].all().limit(count)
        await self.oxen_models['User'].filter(id__in=[u.id for u in users]).delete()
        return len(users)
    
    async def oxenorm_complex_query(self, count: int):
        """Benchmark OxenORM complex query."""
        # Create some posts first
        users = await self.oxen_models['User'].all().limit(count // 10)
        posts = []
        for user in users:
            for i in range(10):
                post = self.oxen_models['Post'](
                    title=f"Post {i} by {user.username}",
                    content=f"Content for post {i}",
                    author_id=user.id
                )
                posts.append(post)
        
        await self.oxen_models['Post'].bulk_create(posts)
        
        # Complex query with joins
        results = await self.oxen_models['Post'].filter(
            title__icontains="Post"
        ).order_by('-created_at').limit(count)
        
        return len(results)
    
    # Tortoise Benchmarks
    async def tortoise_create_users(self, count: int):
        """Benchmark Tortoise user creation."""
        users = []
        for i in range(count):
            user = self.tortoise_models['User'](
                username=f"user_{i}",
                email=f"user_{i}@example.com",
                bio=f"Bio for user {i}"
            )
            users.append(user)
        
        await self.tortoise_models['User'].bulk_create(users)
        return count
    
    async def tortoise_read_users(self, count: int):
        """Benchmark Tortoise user reading."""
        users = await self.tortoise_models['User'].all().limit(count)
        return len(users)
    
    async def tortoise_update_users(self, count: int):
        """Benchmark Tortoise user updating."""
        users = await self.tortoise_models['User'].all().limit(count)
        for user in users:
            user.bio = f"Updated bio for {user.username}"
        
        await self.tortoise_models['User'].bulk_update(users, ['bio'])
        return len(users)
    
    async def tortoise_delete_users(self, count: int):
        """Benchmark Tortoise user deletion."""
        users = await self.tortoise_models['User'].all().limit(count)
        await self.tortoise_models['User'].filter(id__in=[u.id for u in users]).delete()
        return len(users)
    
    async def tortoise_complex_query(self, count: int):
        """Benchmark Tortoise complex query."""
        # Create some posts first
        users = await self.tortoise_models['User'].all().limit(count // 10)
        posts = []
        for user in users:
            for i in range(10):
                post = self.tortoise_models['Post'](
                    title=f"Post {i} by {user.username}",
                    content=f"Content for post {i}",
                    author=user
                )
                posts.append(post)
        
        await self.tortoise_models['Post'].bulk_create(posts)
        
        # Complex query with joins
        results = await self.tortoise_models['Post'].filter(
            title__icontains="Post"
        ).order_by('-created_at').limit(count)
        
        return len(results)
    
    # SQLAlchemy Benchmarks
    async def sqlalchemy_create_users(self, count: int):
        """Benchmark SQLAlchemy user creation."""
        async_session = sessionmaker(
            self.sqlalchemy_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            users = []
            for i in range(count):
                user = self.sqlalchemy_models['User'](
                    username=f"user_{i}",
                    email=f"user_{i}@example.com",
                    bio=f"Bio for user {i}",
                    created_at=sa.func.now()
                )
                users.append(user)
            
            session.add_all(users)
            await session.commit()
        
        return count
    
    async def sqlalchemy_read_users(self, count: int):
        """Benchmark SQLAlchemy user reading."""
        async_session = sessionmaker(
            self.sqlalchemy_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.sqlalchemy_models['User']).limit(count)
            )
            users = result.scalars().all()
        
        return len(users)
    
    async def sqlalchemy_update_users(self, count: int):
        """Benchmark SQLAlchemy user updating."""
        async_session = sessionmaker(
            self.sqlalchemy_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.sqlalchemy_models['User']).limit(count)
            )
            users = result.scalars().all()
            
            for user in users:
                user.bio = f"Updated bio for {user.username}"
            
            await session.commit()
        
        return len(users)
    
    async def sqlalchemy_delete_users(self, count: int):
        """Benchmark SQLAlchemy user deletion."""
        async_session = sessionmaker(
            self.sqlalchemy_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.sqlalchemy_models['User']).limit(count)
            )
            users = result.scalars().all()
            
            for user in users:
                await session.delete(user)
            
            await session.commit()
        
        return len(users)
    
    async def sqlalchemy_complex_query(self, count: int):
        """Benchmark SQLAlchemy complex query."""
        async_session = sessionmaker(
            self.sqlalchemy_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            # Create some posts first
            result = await session.execute(
                sa.select(self.sqlalchemy_models['User']).limit(count // 10)
            )
            users = result.scalars().all()
            
            posts = []
            for user in users:
                for i in range(10):
                    post = self.sqlalchemy_models['Post'](
                        title=f"Post {i} by {user.username}",
                        content=f"Content for post {i}",
                        author_id=user.id,
                        created_at=sa.func.now()
                    )
                    posts.append(post)
            
            session.add_all(posts)
            await session.commit()
            
            # Complex query
            result = await session.execute(
                sa.select(self.sqlalchemy_models['Post'])
                .where(self.sqlalchemy_models['Post'].title.contains("Post"))
                .order_by(self.sqlalchemy_models['Post'].created_at.desc())
                .limit(count)
            )
            posts = result.scalars().all()
        
        return len(posts)
    
    async def run_benchmarks(self, record_counts: List[int] = None) -> BenchmarkSuite:
        """Run all benchmarks."""
        if record_counts is None:
            record_counts = [100, 1000, 10000]
        
        suite = BenchmarkSuite("OxenORM Performance Benchmark")
        
        # Setup database
        await self.setup_database()
        
        try:
            # Define benchmark operations
            operations = [
                ('create_users', 'User Creation'),
                ('read_users', 'User Reading'),
                ('update_users', 'User Updating'),
                ('delete_users', 'User Deletion'),
                ('complex_query', 'Complex Queries')
            ]
            
            # Run benchmarks for each framework
            frameworks = []
            if OXENORM_AVAILABLE:
                frameworks.append(('oxenorm', 'OxenORM'))
            if TORTOISE_AVAILABLE:
                frameworks.append(('tortoise', 'Tortoise ORM'))
            if SQLALCHEMY_AVAILABLE:
                frameworks.append(('sqlalchemy', 'SQLAlchemy'))
            
            for record_count in record_counts:
                print(f"\n🔄 Running benchmarks with {record_count} records...")
                
                for operation, operation_name in operations:
                    for framework_prefix, framework_name in frameworks:
                        operation_func = getattr(self, f"{framework_prefix}_{operation}")
                        
                        print(f"  Testing {framework_name} - {operation_name}...")
                        
                        result = await self.benchmark_operation(
                            operation_name,
                            framework_name,
                            operation_func,
                            record_count
                        )
                        
                        suite.add_result(result)
                        
                        if result.success:
                            print(f"    ✅ {result.duration_ms:.2f}ms, {result.memory_mb:.2f}MB")
                        else:
                            print(f"    ❌ Failed: {result.error_message}")
        
        finally:
            await self.cleanup_database()
        
        # Calculate summary
        suite.calculate_summary()
        return suite
    
    def save_results(self, suite: BenchmarkSuite, filename: str = None):
        """Save benchmark results to file."""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        # Convert results to serializable format
        results_data = []
        for result in suite.results:
            results_data.append({
                'operation': result.operation,
                'framework': result.framework,
                'duration_ms': result.duration_ms,
                'memory_mb': result.memory_mb,
                'records_processed': result.records_processed,
                'success': result.success,
                'error_message': result.error_message,
                'metadata': result.metadata
            })
        
        data = {
            'suite_name': suite.name,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'results': results_data,
            'summary': suite.summary
        }
        
        # Ensure benchmarks directory exists
        os.makedirs('benchmarks', exist_ok=True)
        
        with open(f"benchmarks/{filename}", 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Results saved to benchmarks/{filename}")
    
    def print_summary(self, suite: BenchmarkSuite):
        """Print benchmark summary."""
        print("\n" + "="*60)
        print("📊 BENCHMARK SUMMARY")
        print("="*60)
        
        # Performance ranking
        print("\n🏆 Performance Ranking (Average Duration):")
        for i, (framework, duration) in enumerate(suite.summary['performance_ranking'], 1):
            print(f"  {i}. {framework}: {duration:.2f}ms")
        
        # Framework statistics
        print("\n📈 Framework Statistics:")
        for framework, stats in suite.summary['framework_stats'].items():
            print(f"\n  {framework}:")
            print(f"    Success Rate: {stats['success_rate']:.1%}")
            print(f"    Avg Duration: {stats['avg_duration_ms']:.2f}ms")
            print(f"    Avg Memory: {stats['avg_memory_mb']:.2f}MB")
            print(f"    Operations/sec: {stats['operations_per_second']:.0f}")
            print(f"    Total Records: {stats['total_records_processed']:,}")
        
        # Speedup calculations
        if len(suite.summary['performance_ranking']) > 1:
            fastest = suite.summary['performance_ranking'][0]
            print(f"\n⚡ Speedup vs {fastest[0]}:")
            for framework, duration in suite.summary['performance_ranking'][1:]:
                speedup = duration / fastest[1]
                print(f"  {framework}: {speedup:.1f}x slower")


async def main():
    """Main benchmark function."""
    print("🚀 Starting OxenORM Performance Benchmark Suite")
    print("="*60)
    
    # Check available frameworks
    print("\n📋 Available Frameworks:")
    print(f"  OxenORM: {'✅' if OXENORM_AVAILABLE else '❌'}")
    print(f"  Tortoise ORM: {'✅' if TORTOISE_AVAILABLE else '❌'}")
    print(f"  SQLAlchemy: {'✅' if SQLALCHEMY_AVAILABLE else '❌'}")
    print(f"  Django ORM: {'✅' if DJANGO_AVAILABLE else '❌'}")
    
    if not any([OXENORM_AVAILABLE, TORTOISE_AVAILABLE, SQLALCHEMY_AVAILABLE]):
        print("\n❌ No ORM frameworks available for benchmarking!")
        return
    
    # Run benchmarks
    benchmark = PerformanceBenchmark("sqlite:///benchmark.db")
    suite = await benchmark.run_benchmarks([100, 1000, 10000])
    
    # Print and save results
    benchmark.print_summary(suite)
    benchmark.save_results(suite)


if __name__ == "__main__":
    asyncio.run(main()) 