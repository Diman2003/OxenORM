#!/usr/bin/env python3
"""
Enhanced Migration Runner for OxenORM

This module provides advanced migration execution capabilities including:
- Migration rollback with dependency resolution
- Multi-database migration support
- Transaction management and rollback
- Migration validation and safety checks
- Progress tracking and logging
- Dry-run capabilities
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .models import Migration, MigrationStatus, MigrationPlan
from .enhanced_generator import EnhancedMigrationGenerator


class MigrationExecutionMode(Enum):
    """Migration execution modes."""
    NORMAL = "normal"
    DRY_RUN = "dry_run"
    FORCE = "force"
    TRANSACTION = "transaction"


@dataclass
class MigrationExecutionResult:
    """Result of migration execution."""
    success: bool
    migrations_executed: List[Migration] = field(default_factory=list)
    migrations_failed: List[Migration] = field(default_factory=list)
    execution_time_ms: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    rollback_performed: bool = False


@dataclass
class MigrationDependency:
    """Represents a migration dependency."""
    migration_id: str
    depends_on: List[str] = field(default_factory=list)
    required_by: List[str] = field(default_factory=list)


class EnhancedMigrationRunner:
    """Enhanced migration runner with advanced features."""
    
    def __init__(self, engine, migrations_dir: str = "migrations"):
        self.engine = engine
        self.migrations_dir = migrations_dir
        self.generator = EnhancedMigrationGenerator(engine, migrations_dir)
        self.migrations_table = "oxen_migrations"
        
        # Migration execution state
        self.execution_mode = MigrationExecutionMode.NORMAL
        self.current_transaction = None
        self.execution_log = []
    
    async def run_migrations(
        self, 
        target_version: Optional[str] = None,
        mode: MigrationExecutionMode = MigrationExecutionMode.NORMAL
    ) -> MigrationExecutionResult:
        """Run migrations up to a target version."""
        self.execution_mode = mode
        result = MigrationExecutionResult(success=True)
        
        try:
            # Ensure migrations table exists
            await self._ensure_migrations_table()
            
            # Get pending migrations
            pending_migrations = await self._get_pending_migrations()
            
            if not pending_migrations:
                result.warnings.append("No pending migrations to run")
                return result
            
            # Filter to target version if specified
            if target_version:
                target_migration = self._find_migration_by_version(pending_migrations, target_version)
                if not target_migration:
                    result.success = False
                    result.error_message = f"Target migration version {target_version} not found"
                    return result
                
                pending_migrations = self._filter_migrations_to_target(pending_migrations, target_version)
            
            # Resolve dependencies
            dependency_plan = self._resolve_dependencies(pending_migrations)
            if not dependency_plan.is_valid():
                result.success = False
                result.error_message = f"Dependency conflicts: {dependency_plan.conflicts}"
                return result
            
            # Execute migrations
            if mode == MigrationExecutionMode.DRY_RUN:
                result = await self._dry_run_migrations(pending_migrations)
            else:
                result = await self._execute_migrations(pending_migrations)
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            await self._handle_execution_error(result)
        
        return result
    
    async def rollback_migrations(
        self, 
        target_version: str,
        mode: MigrationExecutionMode = MigrationExecutionMode.NORMAL
    ) -> MigrationExecutionResult:
        """Rollback migrations to a target version."""
        self.execution_mode = mode
        result = MigrationExecutionResult(success=True)
        
        try:
            # Ensure migrations table exists
            await self._ensure_migrations_table()
            
            # Get applied migrations
            applied_migrations = await self._get_applied_migrations()
            
            if not applied_migrations:
                result.warnings.append("No applied migrations to rollback")
                return result
            
            # Find target migration
            target_migration = self._find_migration_by_version(applied_migrations, target_version)
            if not target_migration:
                result.success = False
                result.error_message = f"Target migration version {target_version} not found in applied migrations"
                return result
            
            # Get migrations to rollback
            migrations_to_rollback = self._get_migrations_to_rollback(applied_migrations, target_version)
            
            if not migrations_to_rollback:
                result.warnings.append("No migrations to rollback")
                return result
            
            # Execute rollback
            if mode == MigrationExecutionMode.DRY_RUN:
                result = await self._dry_run_rollback(migrations_to_rollback)
            else:
                result = await self._execute_rollback(migrations_to_rollback)
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            await self._handle_execution_error(result)
        
        return result
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        await self._ensure_migrations_table()
        
        applied_migrations = await self._get_applied_migrations()
        pending_migrations = await self._get_pending_migrations()
        
        return {
            'applied_count': len(applied_migrations),
            'pending_count': len(pending_migrations),
            'applied_migrations': [m.version for m in applied_migrations],
            'pending_migrations': [m.version for m in pending_migrations],
            'last_applied': applied_migrations[-1].version if applied_migrations else None,
            'next_pending': pending_migrations[0].version if pending_migrations else None
        }
    
    async def get_migration_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get migration execution history."""
        await self._ensure_migrations_table()
        
        query = f"""
        SELECT * FROM {self.migrations_table} 
        ORDER BY executed_at DESC 
        LIMIT {limit}
        """
        
        result = await self.engine.execute_query(query)
        
        history = []
        for row in result.rows:
            history.append({
                'version': row['version'],
                'name': row['name'],
                'description': row['description'],
                'status': row['status'],
                'executed_at': row['executed_at'],
                'execution_time_ms': row['execution_time_ms'],
                'error_message': row['error_message']
            })
        
        return history
    
    async def validate_migration_plan(
        self, 
        target_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate a migration plan without executing it."""
        await self._ensure_migrations_table()
        
        pending_migrations = await self._get_pending_migrations()
        
        if target_version:
            pending_migrations = self._filter_migrations_to_target(pending_migrations, target_version)
        
        # Resolve dependencies
        dependency_plan = self._resolve_dependencies(pending_migrations)
        
        # Validate each migration
        validation_results = []
        for migration in pending_migrations:
            validation = await self.generator.validate_migration(migration)
            validation_results.append({
                'version': migration.version,
                'name': migration.name,
                'validation': validation
            })
        
        return {
            'is_valid': dependency_plan.is_valid() and all(
                r['validation']['is_valid'] for r in validation_results
            ),
            'dependency_plan': dependency_plan.get_summary(),
            'validation_results': validation_results,
            'migrations_count': len(pending_migrations)
        }
    
    async def _ensure_migrations_table(self):
        """Ensure the migrations tracking table exists."""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.migrations_table} (
            id VARCHAR(255) PRIMARY KEY,
            version VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            up_sql TEXT NOT NULL,
            down_sql TEXT NOT NULL,
            author VARCHAR(255),
            created_at TIMESTAMP,
            status VARCHAR(50) DEFAULT 'pending',
            executed_at TIMESTAMP,
            execution_time_ms INTEGER,
            error_message TEXT,
            dependencies JSON
        );
        """
        
        await self.engine.execute_query(create_table_sql)
    
    async def _get_applied_migrations(self) -> List[Migration]:
        """Get list of applied migrations."""
        query = f"""
        SELECT * FROM {self.migrations_table} 
        WHERE status = 'completed' 
        ORDER BY executed_at ASC
        """
        
        result = await self.engine.execute_query(query)
        
        migrations = []
        for row in result.rows:
            migration = Migration(
                id=row['id'],
                name=row['name'],
                version=row['version'],
                up_sql=row['up_sql'],
                down_sql=row['down_sql'],
                description=row['description'],
                author=row['author'],
                created_at=row['created_at'],
                status=MigrationStatus(row['status']),
                executed_at=row['executed_at'],
                execution_time_ms=row['execution_time_ms'],
                error_message=row['error_message'],
                dependencies=json.loads(row['dependencies']) if row['dependencies'] else []
            )
            migrations.append(migration)
        
        return migrations
    
    async def _get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        # Get all migration files
        migration_files = self.generator.list_migration_files()
        
        # Load all migrations
        all_migrations = []
        for filepath in migration_files:
            try:
                migration = self.generator.load_migration(filepath)
                all_migrations.append(migration)
            except Exception as e:
                print(f"Warning: Could not load migration from {filepath}: {e}")
        
        # Get applied migrations
        applied_migrations = await self._get_applied_migrations()
        applied_versions = {m.version for m in applied_migrations}
        
        # Filter to pending migrations
        pending_migrations = [
            m for m in all_migrations 
            if m.version not in applied_versions
        ]
        
        # Sort by version
        pending_migrations.sort(key=lambda m: m.version)
        
        return pending_migrations
    
    def _find_migration_by_version(self, migrations: List[Migration], version: str) -> Optional[Migration]:
        """Find a migration by version."""
        for migration in migrations:
            if migration.version == version:
                return migration
        return None
    
    def _filter_migrations_to_target(self, migrations: List[Migration], target_version: str) -> List[Migration]:
        """Filter migrations up to target version."""
        filtered = []
        for migration in migrations:
            filtered.append(migration)
            if migration.version == target_version:
                break
        return filtered
    
    def _resolve_dependencies(self, migrations: List[Migration]) -> MigrationPlan:
        """Resolve migration dependencies."""
        plan = MigrationPlan(migrations_to_run=migrations)
        
        # Build dependency graph
        dependency_graph = {}
        for migration in migrations:
            dependency_graph[migration.id] = {
                'migration': migration,
                'dependencies': set(migration.dependencies),
                'dependents': set()
            }
        
        # Find dependents
        for migration_id, node in dependency_graph.items():
            for dep_id in node['dependencies']:
                if dep_id in dependency_graph:
                    dependency_graph[dep_id]['dependents'].add(migration_id)
        
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id):
            if node_id in rec_stack:
                return True
            if node_id in visited:
                return False
            
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for dep_id in dependency_graph[node_id]['dependencies']:
                if dep_id in dependency_graph and has_cycle(dep_id):
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        # Check for cycles
        for migration_id in dependency_graph:
            if has_cycle(migration_id):
                plan.add_conflict(f"Circular dependency detected involving {migration_id}")
        
        # Topological sort for execution order
        if not plan.conflicts:
            in_degree = {migration_id: len(node['dependencies']) for migration_id, node in dependency_graph.items()}
            queue = [migration_id for migration_id, degree in in_degree.items() if degree == 0]
            sorted_migrations = []
            
            while queue:
                current = queue.pop(0)
                sorted_migrations.append(dependency_graph[current]['migration'])
                
                for dependent in dependency_graph[current]['dependents']:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
            
            if len(sorted_migrations) != len(migrations):
                plan.add_conflict("Dependency resolution failed - some migrations may have unsatisfied dependencies")
            else:
                plan.migrations_to_run = sorted_migrations
                plan.dependencies_resolved = True
        
        return plan
    
    def _get_migrations_to_rollback(self, applied_migrations: List[Migration], target_version: str) -> List[Migration]:
        """Get migrations that need to be rolled back to reach target version."""
        rollback_migrations = []
        target_found = False
        
        for migration in reversed(applied_migrations):
            if migration.version == target_version:
                target_found = True
                break
            rollback_migrations.append(migration)
        
        if not target_found:
            raise ValueError(f"Target migration version {target_version} not found in applied migrations")
        
        return rollback_migrations
    
    async def _execute_migrations(self, migrations: List[Migration]) -> MigrationExecutionResult:
        """Execute a list of migrations."""
        result = MigrationExecutionResult(success=True)
        start_time = datetime.utcnow()
        
        # Start transaction if in transaction mode
        if self.execution_mode == MigrationExecutionMode.TRANSACTION:
            self.current_transaction = await self.engine.begin_transaction()
        
        try:
            for migration in migrations:
                migration_start = datetime.utcnow()
                
                # Execute migration
                await self._execute_single_migration(migration)
                
                # Record execution
                migration.executed_at = datetime.utcnow()
                migration.status = MigrationStatus.COMPLETED
                migration.execution_time_ms = int((migration.executed_at - migration_start).total_seconds() * 1000)
                
                # Save to database
                await self._save_migration_execution(migration)
                
                result.migrations_executed.append(migration)
                
                # Log execution
                self._log_execution(f"✅ Executed migration {migration.version}: {migration.name}")
            
            # Commit transaction if in transaction mode
            if self.current_transaction:
                await self.engine.execute_query(f"COMMIT;")
                self.current_transaction = None
            
            result.execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
        except Exception as e:
            # Rollback transaction if in transaction mode
            if self.current_transaction:
                await self.engine.execute_query(f"ROLLBACK;")
                self.current_transaction = None
            
            result.success = False
            result.error_message = str(e)
            result.migrations_failed.append(migration)
            
            # Mark failed migration
            migration.status = MigrationStatus.FAILED
            migration.error_message = str(e)
            await self._save_migration_execution(migration)
        
        return result
    
    async def _execute_rollback(self, migrations: List[Migration]) -> MigrationExecutionResult:
        """Execute rollback for a list of migrations."""
        result = MigrationExecutionResult(success=True, rollback_performed=True)
        start_time = datetime.utcnow()
        
        # Start transaction if in transaction mode
        if self.execution_mode == MigrationExecutionMode.TRANSACTION:
            self.current_transaction = await self.engine.begin_transaction()
        
        try:
            for migration in migrations:
                migration_start = datetime.utcnow()
                
                # Execute rollback
                await self._execute_single_rollback(migration)
                
                # Record rollback
                migration.status = MigrationStatus.ROLLED_BACK
                migration.execution_time_ms = int((datetime.utcnow() - migration_start).total_seconds() * 1000)
                
                # Update database record
                await self._update_migration_status(migration)
                
                result.migrations_executed.append(migration)
                
                # Log rollback
                self._log_execution(f"⏪ Rolled back migration {migration.version}: {migration.name}")
            
            # Commit transaction if in transaction mode
            if self.current_transaction:
                await self.engine.execute_query(f"COMMIT;")
                self.current_transaction = None
            
            result.execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
        except Exception as e:
            # Rollback transaction if in transaction mode
            if self.current_transaction:
                await self.engine.execute_query(f"ROLLBACK;")
                self.current_transaction = None
            
            result.success = False
            result.error_message = str(e)
            result.migrations_failed.append(migration)
        
        return result
    
    async def _execute_single_migration(self, migration: Migration):
        """Execute a single migration."""
        # Execute UP migration
        await self.engine.execute_query(migration.up_sql)
    
    async def _execute_single_rollback(self, migration: Migration):
        """Execute rollback for a single migration."""
        # Execute DOWN migration
        await self.engine.execute_query(migration.down_sql)
    
    async def _save_migration_execution(self, migration: Migration):
        """Save migration execution record to database."""
        query = f"""
        INSERT INTO {self.migrations_table} (
            id, version, name, description, up_sql, down_sql, author, 
            created_at, status, executed_at, execution_time_ms, error_message, dependencies
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = [
            migration.id,
            migration.version,
            migration.name,
            migration.description,
            migration.up_sql,
            migration.down_sql,
            migration.author,
            migration.created_at,
            migration.status.value,
            migration.executed_at,
            migration.execution_time_ms,
            migration.error_message,
            json.dumps(migration.dependencies)
        ]
        
        await self.engine.execute_query(query, params)
    
    async def _update_migration_status(self, migration: Migration):
        """Update migration status in database."""
        query = f"""
        UPDATE {self.migrations_table} 
        SET status = ?, execution_time_ms = ? 
        WHERE version = ?
        """
        
        params = [
            migration.status.value,
            migration.execution_time_ms,
            migration.version
        ]
        
        await self.engine.execute_query(query, params)
    
    async def _dry_run_migrations(self, migrations: List[Migration]) -> MigrationExecutionResult:
        """Perform a dry run of migrations."""
        result = MigrationExecutionResult(success=True)
        
        for migration in migrations:
            # Validate migration
            validation = await self.generator.validate_migration(migration)
            if not validation['is_valid']:
                result.warnings.extend(validation['errors'])
            
            result.migrations_executed.append(migration)
        
        result.warnings.append(f"Dry run: Would execute {len(migrations)} migrations")
        return result
    
    async def _dry_run_rollback(self, migrations: List[Migration]) -> MigrationExecutionResult:
        """Perform a dry run of rollback."""
        result = MigrationExecutionResult(success=True, rollback_performed=True)
        
        for migration in migrations:
            result.migrations_executed.append(migration)
        
        result.warnings.append(f"Dry run: Would rollback {len(migrations)} migrations")
        return result
    
    async def _handle_execution_error(self, result: MigrationExecutionResult):
        """Handle execution errors."""
        self._log_execution(f"❌ Migration execution failed: {result.error_message}")
        
        # Rollback transaction if active
        if self.current_transaction:
            await self.engine.execute_query(f"ROLLBACK;")
            self.current_transaction = None
    
    def _log_execution(self, message: str):
        """Log execution message."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.execution_log.append(log_entry)
        print(log_entry) 