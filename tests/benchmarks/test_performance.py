"""
Performance Benchmarks for OxenORM

This module contains benchmarks comparing OxenORM performance against
SQLAlchemy and Tortoise ORM.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import tempfile
import os

# Try to import comparison ORMs
try:
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import declarative_base, sessionmaker
    from sqlalchemy import Column, Integer, String, Boolean, DateTime
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

try:
    from tortoise import Tortoise, fields
    from tortoise.models import Model as TortoiseModel
    TORTOISE_AVAILABLE = True
except ImportError:
    TORTOISE_AVAILABLE = False

from oxen import Model, init_db, close_db
from oxen.fields import IntField, CharField, BooleanField, DateTimeField


class BenchmarkUser(Model):
    """User model for benchmarking."""
    
    id = IntField(primary_key=True)
    username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100, unique=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        table = "benchmark_users"


# SQLAlchemy models for comparison
if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
    class SQLAlchemyUser(Base):
        __tablename__ = "benchmark_users"
        
        id = Column(Integer, primary_key=True)
        username = Column(String(50), unique=True)
        email = Column(String(100), unique=True)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime)


# Tortoise models for comparison
if TORTOISE_AVAILABLE:
    class TortoiseUser(TortoiseModel):
        id = fields.IntField(pk=True)
        username = fields.CharField(max_length=50, unique=True)
        email = fields.CharField(max_length=100, unique=True)
        is_active = fields.BooleanField(default=True)
        created_at = fields.DatetimeField(auto_now_add=True)
        
        class Meta:
            table = "benchmark_users"


class BenchmarkResult:
    """Container for benchmark results."""
    
    def __init__(self, name: str, times: List[float]):
        self.name = name
        self.times = times
        self.mean = statistics.mean(times)
        self.median = statistics.median(times)
        self.min = min(times)
        self.max = max(times)
        self.std = statistics.stdev(times) if len(times) > 1 else 0
    
    def __str__(self) -> str:
        return (f"{self.name}: "
                f"mean={self.mean:.4f}s, "
                f"median={self.median:.4f}s, "
                f"min={self.min:.4f}s, "
                f"max={self.max:.4f}s, "
                f"std={self.std:.4f}s")


class PerformanceBenchmark:
    """Performance benchmarking suite."""
    
    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results: Dict[str, BenchmarkResult] = {}
    
    async def benchmark_oxenorm(self, db_url: str) -> BenchmarkResult:
        """Benchmark OxenORM operations."""
        await init_db({'default': db_url})
        
        times = []
        
        try:
            for i in range(self.iterations):
                start_time = time.time()
                
                # Create user
                user = await BenchmarkUser.create(
                    username=f"user{i}",
                    email=f"user{i}@example.com"
                )
                
                # Get user
                retrieved_user = await BenchmarkUser.get(id=user.id)
                
                # Update user
                user.is_active = False
                await user.save()
                
                # Delete user
                await user.delete()
                
                end_time = time.time()
                times.append(end_time - start_time)
                
        finally:
            await close_db()
        
        return BenchmarkResult("OxenORM", times)
    
    async def benchmark_tortoise(self, db_url: str) -> BenchmarkResult:
        """Benchmark Tortoise ORM operations."""
        if not TORTOISE_AVAILABLE:
            return BenchmarkResult("Tortoise ORM", [0.0])
        
        await Tortoise.init(db_url=db_url, modules={'models': ['__main__']})
        await Tortoise.generate_schemas()
        
        times = []
        
        try:
            for i in range(self.iterations):
                start_time = time.time()
                
                # Create user
                user = await TortoiseUser.create(
                    username=f"user{i}",
                    email=f"user{i}@example.com"
                )
                
                # Get user
                retrieved_user = await TortoiseUser.get(id=user.id)
                
                # Update user
                user.is_active = False
                await user.save()
                
                # Delete user
                await user.delete()
                
                end_time = time.time()
                times.append(end_time - start_time)
                
        finally:
            await Tortoise.close_connections()
        
        return BenchmarkResult("Tortoise ORM", times)
    
    async def benchmark_sqlalchemy(self, db_url: str) -> BenchmarkResult:
        """Benchmark SQLAlchemy operations."""
        if not SQLALCHEMY_AVAILABLE:
            return BenchmarkResult("SQLAlchemy", [0.0])
        
        engine = create_async_engine(db_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        times = []
        
        try:
            for i in range(self.iterations):
                start_time = time.time()
                
                async with async_session() as session:
                    # Create user
                    user = SQLAlchemyUser(
                        username=f"user{i}",
                        email=f"user{i}@example.com"
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                    
                    # Get user
                    retrieved_user = await session.get(SQLAlchemyUser, user.id)
                    
                    # Update user
                    user.is_active = False
                    await session.commit()
                    
                    # Delete user
                    await session.delete(user)
                    await session.commit()
                
                end_time = time.time()
                times.append(end_time - start_time)
                
        finally:
            await engine.dispose()
        
        return BenchmarkResult("SQLAlchemy", times)
    
    async def benchmark_bulk_operations(self, db_url: str) -> BenchmarkResult:
        """Benchmark bulk insert operations."""
        await init_db({'default': db_url})
        
        times = []
        
        try:
            for i in range(self.iterations // 10):  # Fewer iterations for bulk ops
                start_time = time.time()
                
                # Create multiple users
                users = []
                for j in range(100):
                    user = BenchmarkUser(
                        username=f"bulk{i}_{j}",
                        email=f"bulk{i}_{j}@example.com"
                    )
                    users.append(user)
                
                # Bulk create (when implemented)
                # await BenchmarkUser.bulk_create(users)
                
                # For now, create individually
                for user in users:
                    await BenchmarkUser.create(
                        username=user.username,
                        email=user.email
                    )
                
                end_time = time.time()
                times.append(end_time - start_time)
                
        finally:
            await close_db()
        
        return BenchmarkResult("OxenORM Bulk Insert", times)
    
    async def benchmark_query_operations(self, db_url: str) -> BenchmarkResult:
        """Benchmark query operations."""
        await init_db({'default': db_url})
        
        # Create test data
        for i in range(1000):
            await BenchmarkUser.create(
                username=f"query{i}",
                email=f"query{i}@example.com",
                is_active=i % 2 == 0
            )
        
        times = []
        
        try:
            for i in range(self.iterations):
                start_time = time.time()
                
                # Complex query operations
                active_users = await BenchmarkUser.filter(is_active=True)
                total_count = await BenchmarkUser.count()
                recent_users = await BenchmarkUser.all().order_by("-created_at").limit(10)
                
                end_time = time.time()
                times.append(end_time - start_time)
                
        finally:
            await close_db()
        
        return BenchmarkResult("OxenORM Query", times)
    
    def print_results(self):
        """Print benchmark results."""
        print("\n" + "="*80)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("="*80)
        
        for name, result in self.results.items():
            print(f"\n{result}")
        
        # Calculate speedups
        if "OxenORM" in self.results and "Tortoise ORM" in self.results:
            oxenorm_mean = self.results["OxenORM"].mean
            tortoise_mean = self.results["Tortoise ORM"].mean
            if tortoise_mean > 0:
                speedup = tortoise_mean / oxenorm_mean
                print(f"\nOxenORM vs Tortoise ORM speedup: {speedup:.2f}x")
        
        if "OxenORM" in self.results and "SQLAlchemy" in self.results:
            oxenorm_mean = self.results["OxenORM"].mean
            sqlalchemy_mean = self.results["SQLAlchemy"].mean
            if sqlalchemy_mean > 0:
                speedup = sqlalchemy_mean / oxenorm_mean
                print(f"OxenORM vs SQLAlchemy speedup: {speedup:.2f}x")
        
        print("\n" + "="*80)


async def run_benchmarks():
    """Run all benchmarks."""
    # Create temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_url = f"sqlite:{db_path}"
    
    try:
        benchmark = PerformanceBenchmark(iterations=50)
        
        print("Running OxenORM benchmarks...")
        benchmark.results["OxenORM"] = await benchmark.benchmark_oxenorm(db_url)
        
        print("Running Tortoise ORM benchmarks...")
        benchmark.results["Tortoise ORM"] = await benchmark.benchmark_tortoise(db_url)
        
        print("Running SQLAlchemy benchmarks...")
        benchmark.results["SQLAlchemy"] = await benchmark.benchmark_sqlalchemy(db_url)
        
        print("Running bulk operation benchmarks...")
        benchmark.results["OxenORM Bulk"] = await benchmark.benchmark_bulk_operations(db_url)
        
        print("Running query operation benchmarks...")
        benchmark.results["OxenORM Query"] = await benchmark.benchmark_query_operations(db_url)
        
        benchmark.print_results()
        
    finally:
        # Cleanup
        try:
            os.unlink(db_path)
        except OSError:
            pass


if __name__ == "__main__":
    asyncio.run(run_benchmarks()) 