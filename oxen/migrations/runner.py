"""
Migration execution and management.
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import Migration, MigrationStatus, MigrationPlan
from .generator import MigrationGenerator


class MigrationRunner:
    """Executes and manages database migrations."""
    
    def __init__(self, engine, migrations_dir: str = "migrations"):
        self.engine = engine
        self.migrations_dir = migrations_dir
        self.generator = MigrationGenerator(engine, migrations_dir)
    
    async def _ensure_migrations_table(self):
        """Ensure the migrations tracking table exists."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS oxen_migrations (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            version VARCHAR(255) NOT NULL UNIQUE,
            up_sql TEXT NOT NULL,
            down_sql TEXT NOT NULL,
            description TEXT,
            author VARCHAR(255),
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            executed_at TIMESTAMP,
            execution_time_ms INTEGER,
            error_message TEXT
        )
        """
        
        await self.engine.execute_query(create_table_sql)
    
    async def get_applied_migrations(self) -> List[Migration]:
        """Get list of migrations that have been applied to the database."""
        sql = """
        SELECT 
            id, name, version, up_sql, down_sql, description, author,
            status, created_at, executed_at, execution_time_ms, error_message
        FROM oxen_migrations 
        WHERE status = 'completed'
        ORDER BY version
        """
        
        result = await self.engine.execute_query(sql)
        migrations = []
        
        for row in result['data']:
            migration = Migration.from_dict(row)
            migrations.append(migration)
        
        return migrations
    
    async def get_pending_migrations(self) -> List[Migration]:
        """Get list of migrations that haven't been applied yet."""
        applied_versions = {m.version for m in await self.get_applied_migrations()}
        pending_migrations = []
        
        for filepath in self.generator.list_migrations():
            migration = self.generator.load_migration_from_file(filepath)
            if migration.version not in applied_versions:
                pending_migrations.append(migration)
        
        return sorted(pending_migrations, key=lambda m: m.version)
    
    async def create_migration_plan(self, target_version: Optional[str] = None) -> MigrationPlan:
        """Create a plan for migration execution."""
        applied_migrations = await self.get_applied_migrations()
        pending_migrations = await self.get_pending_migrations()
        
        plan = MigrationPlan(
            migrations_to_run=[],
            migrations_to_rollback=[],
            dependencies_resolved=True
        )
        
        if target_version is None:
            # Run all pending migrations
            plan.migrations_to_run = pending_migrations
        else:
            # Find target migration
            target_migration = None
            for migration in pending_migrations:
                if migration.version == target_version:
                    target_migration = migration
                    break
            
            if target_migration:
                # Run migrations up to target
                for migration in pending_migrations:
                    if migration.version <= target_version:
                        plan.migrations_to_run.append(migration)
            else:
                # Check if we need to rollback
                for migration in applied_migrations:
                    if migration.version > target_version:
                        plan.migrations_to_rollback.append(migration)
        
        # Resolve dependencies
        plan.dependencies_resolved = self._resolve_dependencies(plan)
        
        return plan
    
    def _resolve_dependencies(self, plan: MigrationPlan) -> bool:
        """Resolve migration dependencies and check for conflicts."""
        # Simple dependency resolution - in practice, you'd want more sophisticated logic
        applied_versions = set()
        
        # Check dependencies for migrations to run
        for migration in plan.migrations_to_run:
            for dep_version in migration.dependencies:
                if dep_version not in applied_versions:
                    plan.add_conflict(f"Migration {migration.version} depends on {dep_version} which is not applied")
                    return False
            applied_versions.add(migration.version)
        
        return True
    
    async def run_migration(self, migration: Migration) -> bool:
        """Run a single migration."""
        start_time = time.time()
        
        try:
            # Update status to running
            await self._update_migration_status(migration.id, MigrationStatus.RUNNING)
            
            # Execute the migration SQL
            await self.engine.execute_query(migration.up_sql)
            
            # Update status to completed
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._update_migration_completed(
                migration.id, 
                MigrationStatus.COMPLETED, 
                execution_time_ms
            )
            
            return True
            
        except Exception as e:
            # Update status to failed
            await self._update_migration_failed(migration.id, str(e))
            return False
    
    async def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a single migration."""
        start_time = time.time()
        
        try:
            # Update status to running
            await self._update_migration_status(migration.id, MigrationStatus.RUNNING)
            
            # Execute the rollback SQL
            await self.engine.execute_query(migration.down_sql)
            
            # Update status to rolled back
            execution_time_ms = int((time.time() - start_time) * 1000)
            await self._update_migration_completed(
                migration.id, 
                MigrationStatus.ROLLED_BACK, 
                execution_time_ms
            )
            
            return True
            
        except Exception as e:
            # Update status to failed
            await self._update_migration_failed(migration.id, str(e))
            return False
    
    async def _update_migration_status(self, migration_id: str, status: MigrationStatus):
        """Update migration status in database."""
        sql = """
        UPDATE oxen_migrations 
        SET status = $1, executed_at = CURRENT_TIMESTAMP
        WHERE id = $2
        """
        await self.engine.execute_query(sql, [status.value, migration_id])
    
    async def _update_migration_completed(self, migration_id: str, status: MigrationStatus, execution_time_ms: int):
        """Update migration as completed."""
        sql = """
        UPDATE oxen_migrations 
        SET status = $1, executed_at = CURRENT_TIMESTAMP, execution_time_ms = $2
        WHERE id = $3
        """
        await self.engine.execute_query(sql, [status.value, execution_time_ms, migration_id])
    
    async def _update_migration_failed(self, migration_id: str, error_message: str):
        """Update migration as failed."""
        sql = """
        UPDATE oxen_migrations 
        SET status = 'failed', executed_at = CURRENT_TIMESTAMP, error_message = $1
        WHERE id = $2
        """
        await self.engine.execute_query(sql, [error_message, migration_id])
    
    async def record_migration(self, migration: Migration):
        """Record a migration in the database."""
        sql = """
        INSERT INTO oxen_migrations (
            id, name, version, up_sql, down_sql, description, author,
            status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        await self.engine.execute_query(sql, [
            migration.id,
            migration.name,
            migration.version,
            migration.up_sql,
            migration.down_sql,
            migration.description,
            migration.author,
            migration.status.value
        ])
    
    async def run_migrations(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """Run migrations up to a target version."""
        plan = await self.create_migration_plan(target_version)
        
        if not plan.is_valid():
            return {
                'success': False,
                'error': 'Migration plan is invalid',
                'conflicts': plan.conflicts
            }
        
        results = {
            'success': True,
            'migrations_run': 0,
            'migrations_failed': 0,
            'execution_time_ms': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        # Run migrations
        for migration in plan.migrations_to_run:
            # Check if migration is already recorded
            existing_migrations = await self.get_applied_migrations()
            existing_versions = {m.version for m in existing_migrations}
            
            if migration.version not in existing_versions:
                # Record migration if not already recorded
                await self.record_migration(migration)
            
            success = await self.run_migration(migration)
            if success:
                results['migrations_run'] += 1
            else:
                results['migrations_failed'] += 1
                results['errors'].append(f"Migration {migration.version} failed")
                results['success'] = False
        
        results['execution_time_ms'] = int((time.time() - start_time) * 1000)
        
        return results
    
    async def rollback_migrations(self, target_version: str) -> Dict[str, Any]:
        """Rollback migrations to a target version."""
        plan = await self.create_migration_plan(target_version)
        
        results = {
            'success': True,
            'migrations_rolled_back': 0,
            'migrations_failed': 0,
            'execution_time_ms': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        # Rollback migrations in reverse order
        for migration in reversed(plan.migrations_to_rollback):
            success = await self.rollback_migration(migration)
            if success:
                results['migrations_rolled_back'] += 1
            else:
                results['migrations_failed'] += 1
                results['errors'].append(f"Rollback of migration {migration.version} failed")
                results['success'] = False
        
        results['execution_time_ms'] = int((time.time() - start_time) * 1000)
        
        return results
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        applied_migrations = await self.get_applied_migrations()
        pending_migrations = await self.get_pending_migrations()
        
        return {
            'applied_count': len(applied_migrations),
            'pending_count': len(pending_migrations),
            'current_version': applied_migrations[-1].version if applied_migrations else None,
            'latest_version': pending_migrations[-1].version if pending_migrations else None,
            'applied_migrations': [m.version for m in applied_migrations],
            'pending_migrations': [m.version for m in pending_migrations]
        } 