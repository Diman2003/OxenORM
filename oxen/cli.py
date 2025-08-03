#!/usr/bin/env python3
"""
OxenORM Command Line Interface

Provides comprehensive CLI tools for database management, migrations,
and development utilities.
"""

import asyncio
import click
import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .engine import UnifiedEngine, connect, disconnect
from .models import Model
from .migrations import MigrationEngine


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """OxenORM - High-Performance Python ORM with Rust Backend"""
    pass


@cli.group()
def db():
    """Database management commands"""
    pass


@db.command()
@click.option('--url', '-u', required=True, help='Database connection URL')
@click.option('--type', '-t', default='sqlite', help='Database type (sqlite, postgres, mysql)')
def init(url: str, type: str):
    """Initialize database connection and create tables"""
    async def _init():
        try:
            engine = await connect(url)
            click.echo(f"✅ Connected to database: {url}")
            
            # Get database info
            info = engine.get_backend_info()
            click.echo(f"📊 Database Type: {info['backend']}")
            click.echo(f"🔗 Connection: {info['connected']}")
            
            await disconnect(engine)
            click.echo("✅ Database initialization completed")
            
        except Exception as e:
            click.echo(f"❌ Database initialization failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_init())


@db.command()
@click.option('--url', '-u', required=True, help='Database connection URL')
def status(url: str):
    """Check database connection status"""
    async def _status():
        try:
            engine = await connect(url)
            info = engine.get_backend_info()
            
            click.echo("📊 Database Status:")
            click.echo(f"  Connection: {url}")
            click.echo(f"  Status: {'🟢 Connected' if info['connected'] else '🔴 Disconnected'}")
            click.echo(f"  Backend: {info['backend']}")
            click.echo(f"  Rust Available: {info['rust_available']}")
            
            # Performance stats
            stats = engine.performance_monitor.get_stats()
            click.echo(f"  Total Queries: {stats['total_queries']}")
            click.echo(f"  Average Time: {stats['average_time']:.3f}s")
            
            await disconnect(engine)
            
        except Exception as e:
            click.echo(f"❌ Status check failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_status())


@cli.group()
def migrate():
    """Migration management commands"""
    pass


@migrate.command()
@click.option('--url', '-u', required=True, help='Database connection URL')
@click.option('--app', '-a', help='Specific app to migrate')
def makemigrations(url: str, app: Optional[str]):
    """Generate new migration files"""
    async def _makemigrations():
        try:
            engine = await connect(url)
            migration_engine = MigrationEngine(engine)
            
            # Generate migrations
            migrations = await migration_engine.generate_migrations(app)
            
            if migrations:
                click.echo(f"✅ Generated {len(migrations)} migration(s):")
                for migration in migrations:
                    click.echo(f"  📝 {migration['name']}")
            else:
                click.echo("ℹ️  No new migrations needed")
            
            await disconnect(engine)
            
        except Exception as e:
            click.echo(f"❌ Migration generation failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_makemigrations())


@migrate.command()
@click.option('--url', '-u', required=True, help='Database connection URL')
@click.option('--app', '-a', help='Specific app to migrate')
@click.option('--fake', is_flag=True, help='Mark migrations as applied without running them')
def apply_migrations(url: str, app: Optional[str], fake: bool):
    """Apply pending migrations"""
    async def _migrate():
        try:
            engine = await connect(url)
            migration_engine = MigrationEngine(engine)
            
            # Apply migrations
            applied = await migration_engine.apply_migrations(app, fake=fake)
            
            if applied:
                click.echo(f"✅ Applied {len(applied)} migration(s):")
                for migration in applied:
                    click.echo(f"  ✅ {migration['name']}")
            else:
                click.echo("ℹ️  No pending migrations")
            
            await disconnect(engine)
            
        except Exception as e:
            click.echo(f"❌ Migration failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_migrate())


@migrate.command()
@click.option('--url', '-u', required=True, help='Database connection URL')
@click.option('--app', '-a', help='Specific app to migrate')
def showmigrations(url: str, app: Optional[str]):
    """Show migration status"""
    async def _showmigrations():
        try:
            engine = await connect(url)
            migration_engine = MigrationEngine(engine)
            
            # Get migration status
            status = await migration_engine.get_migration_status(app)
            
            click.echo("📋 Migration Status:")
            for app_name, migrations in status.items():
                click.echo(f"\n📁 {app_name}:")
                for migration in migrations:
                    status_icon = "✅" if migration['applied'] else "⏳"
                    click.echo(f"  {status_icon} {migration['name']}")
            
            await disconnect(engine)
            
        except Exception as e:
            click.echo(f"❌ Failed to show migrations: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_showmigrations())


@cli.group()
def shell():
    """Interactive shell commands"""
    pass


@shell.command()
@click.option('--url', '-u', required=True, help='Database connection URL')
@click.option('--models', '-m', help='Comma-separated list of model modules to import')
def start_shell(url: str, models: Optional[str]):
    """Start interactive Python shell with database connection"""
    async def _shell():
        try:
            engine = await connect(url)
            
            # Import models if specified
            model_imports = ""
            if models:
                for model_module in models.split(','):
                    model_imports += f"from {model_module.strip()} import *\n"
            
            # Create shell startup script
            startup_script = f"""
import asyncio
from oxen import connect, disconnect

# Database connection
engine = None

async def connect_db():
    global engine
    engine = await connect("{url}")
    print(f"✅ Connected to database: {url}")

async def disconnect_db():
    global engine
    if engine:
        await disconnect(engine)
        print("✅ Disconnected from database")

# Auto-connect on startup
asyncio.create_task(connect_db())

{model_imports}

print("🐂 OxenORM Interactive Shell")
print("Available: engine, connect_db(), disconnect_db()")
print("Use 'await connect_db()' to reconnect if needed")
"""
            
            # Write startup script
            startup_file = Path.home() / ".oxen_shell_startup.py"
            startup_file.write_text(startup_script)
            
            # Start IPython or regular Python shell
            try:
                import IPython
                IPython.start_ipython(argv=[], user_ns={
                    'engine': engine,
                    'connect_db': lambda: asyncio.create_task(connect_db()),
                    'disconnect_db': lambda: asyncio.create_task(disconnect_db())
                })
            except ImportError:
                import code
                code.interact(local={
                    'engine': engine,
                    'connect_db': lambda: asyncio.create_task(connect_db()),
                    'disconnect_db': lambda: asyncio.create_task(disconnect_db())
                })
            
        except Exception as e:
            click.echo(f"❌ Shell startup failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_shell())


@cli.group()
def test():
    """Testing commands"""
    pass


@test.command()
@click.option('--url', '-u', required=True, help='Database connection URL')
@click.option('--pattern', '-p', default='test_*.py', help='Test file pattern')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(url: str, pattern: str, verbose: bool):
    """Run tests with database connection"""
    async def _run_tests():
        try:
            engine = await connect(url)
            
            # Run pytest
            import pytest
            args = ['-x', pattern]
            if verbose:
                args.append('-v')
            
            exit_code = pytest.main(args)
            
            await disconnect(engine)
            sys.exit(exit_code)
            
        except Exception as e:
            click.echo(f"❌ Test execution failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_run_tests())


@cli.group()
def benchmark():
    """Performance benchmarking commands"""
    pass


@benchmark.command()
@click.option('--url', '-u', required=True, help='Database connection URL')
@click.option('--iterations', '-i', default=1000, help='Number of iterations')
@click.option('--output', '-o', help='Output file for results')
def performance(url: str, iterations: int, output: Optional[str]):
    """Run performance benchmarks"""
    async def _benchmark():
        try:
            engine = await connect(url)
            
            # Run benchmarks
            results = await run_performance_benchmarks(engine, iterations)
            
            # Display results
            click.echo("📊 Performance Benchmark Results:")
            click.echo(f"  Total Queries: {results['total_queries']}")
            click.echo(f"  Average Time: {results['average_time']:.3f}ms")
            click.echo(f"  Min Time: {results['min_time']:.3f}ms")
            click.echo(f"  Max Time: {results['max_time']:.3f}ms")
            click.echo(f"  Queries/Second: {results['qps']:.0f}")
            
            # Save results if output specified
            if output:
                with open(output, 'w') as f:
                    json.dump(results, f, indent=2)
                click.echo(f"💾 Results saved to: {output}")
            
            await disconnect(engine)
            
        except Exception as e:
            click.echo(f"❌ Benchmark failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_benchmark())


async def run_performance_benchmarks(engine: UnifiedEngine, iterations: int) -> Dict[str, Any]:
    """Run comprehensive performance benchmarks"""
    import time
    
    results = {
        'total_queries': 0,
        'times': [],
        'average_time': 0,
        'min_time': 0,
        'max_time': 0,
        'qps': 0
    }
    
    # Simple query benchmark
    for i in range(iterations):
        start_time = time.time()
        await engine.execute_query("SELECT 1")
        end_time = time.time()
        
        results['times'].append((end_time - start_time) * 1000)  # Convert to ms
        results['total_queries'] += 1
    
    # Calculate statistics
    times = results['times']
    results['average_time'] = sum(times) / len(times)
    results['min_time'] = min(times)
    results['max_time'] = max(times)
    results['qps'] = iterations / (sum(times) / 1000)  # Queries per second
    
    return results


@cli.command()
@click.option('--url', '-u', required=True, help='Database connection URL')
@click.option('--output', '-o', help='Output file for schema')
def inspect(url: str, output: Optional[str]):
    """Inspect database schema"""
    async def _inspect():
        try:
            engine = await connect(url)
            
            # Get schema information
            schema = await inspect_database_schema(engine)
            
            # Display schema
            click.echo("📋 Database Schema:")
            for table_name, table_info in schema.items():
                click.echo(f"\n📊 Table: {table_name}")
                for column in table_info['columns']:
                    nullable = "NULL" if column['nullable'] else "NOT NULL"
                    click.echo(f"  📝 {column['name']}: {column['type']} {nullable}")
                
                if table_info['indexes']:
                    click.echo("  🔍 Indexes:")
                    for index in table_info['indexes']:
                        click.echo(f"    - {index['name']}: {', '.join(index['columns'])}")
            
            # Save schema if output specified
            if output:
                with open(output, 'w') as f:
                    json.dump(schema, f, indent=2)
                click.echo(f"\n💾 Schema saved to: {output}")
            
            await disconnect(engine)
            
        except Exception as e:
            click.echo(f"❌ Schema inspection failed: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_inspect())


async def inspect_database_schema(engine: UnifiedEngine) -> Dict[str, Any]:
    """Inspect database schema and return table information"""
    schema = {}
    
    # Get list of tables
    tables_result = await engine.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    
    for table_row in tables_result.get('data', []):
        table_name = table_row[0]
        
        # Get table schema
        schema_result = await engine.execute_query(f"PRAGMA table_info({table_name})")
        
        columns = []
        for col_row in schema_result.get('data', []):
            columns.append({
                'name': col_row[1],
                'type': col_row[2],
                'nullable': not col_row[3],
                'primary_key': bool(col_row[5])
            })
        
        # Get indexes
        indexes_result = await engine.execute_query(f"PRAGMA index_list({table_name})")
        
        indexes = []
        for idx_row in indexes_result.get('data', []):
            index_name = idx_row[1]
            index_info_result = await engine.execute_query(f"PRAGMA index_info({index_name})")
            
            index_columns = []
            for info_row in index_info_result.get('data', []):
                index_columns.append(info_row[2])
            
            indexes.append({
                'name': index_name,
                'columns': index_columns
            })
        
        schema[table_name] = {
            'columns': columns,
            'indexes': indexes
        }
    
    return schema


def main():
    """Main entry point for the CLI"""
    cli()


if __name__ == '__main__':
    main() 