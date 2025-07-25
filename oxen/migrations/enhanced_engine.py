#!/usr/bin/env python3
"""
Enhanced Migration Engine for OxenORM

This module provides a unified interface for all migration operations including:
- Automatic migration generation from model changes
- Multi-database migration support
- Advanced rollback capabilities
- Migration validation and safety checks
- Schema comparison and diffing
- Migration templates and customization
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

from .models import Migration, MigrationStatus, MigrationPlan, SchemaDiff
from .enhanced_generator import EnhancedMigrationGenerator, MigrationType
from .enhanced_runner import EnhancedMigrationRunner, MigrationExecutionMode, MigrationExecutionResult


@dataclass
class MigrationConfig:
    """Configuration for migration operations."""
    migrations_dir: str = "migrations"
    auto_generate: bool = True
    validate_before_run: bool = True
    use_transactions: bool = True
    backup_before_migration: bool = False
    max_rollback_depth: int = 10
    allowed_dangerous_operations: List[str] = None


class EnhancedMigrationEngine:
    """Enhanced migration engine with advanced features."""
    
    def __init__(self, engine, config: Optional[MigrationConfig] = None):
        self.engine = engine
        self.config = config or MigrationConfig()
        
        # Initialize components
        self.generator = EnhancedMigrationGenerator(engine, self.config.migrations_dir)
        self.runner = EnhancedMigrationRunner(engine, self.config.migrations_dir)
        
        # Multi-database support
        self.database_engines = {}
        self.current_database = "default"
    
    # ============================================================================
    # MIGRATION GENERATION
    # ============================================================================
    
    async def makemigrations(
        self,
        models: Optional[List[Any]] = None,
        description: str = "Auto-generated migration",
        author: Optional[str] = None,
        detect_changes: bool = True
    ) -> Migration:
        """Generate a new migration from model changes."""
        if detect_changes and models:
            # Compare with current database schema
            current_schema = await self.get_current_schema()
            model_schema = await self.generator._extract_schema_from_models(models)
            
            # Generate diff
            diff = await self.generator._compare_schemas(current_schema, model_schema)
            
            if not diff.has_changes():
                raise ValueError("No schema changes detected")
            
            # Generate migration from diff
            migration = await self.generator.generate_migration_from_diff(diff, description, author)
        else:
            # Create empty migration
            migration = await self.generator.generate_data_migration(
                up_sql="-- TODO: Add your migration SQL here",
                down_sql="-- TODO: Add your rollback SQL here",
                description=description,
                author=author
            )
        
        # Save migration
        filepath = self.generator.save_migration(migration)
        
        # Validate migration if configured
        if self.config.validate_before_run:
            validation = await self.generator.validate_migration(migration)
            if not validation['is_valid']:
                print("⚠️  Migration validation warnings:")
                for warning in validation['warnings']:
                    print(f"   - {warning}")
        
        return migration
    
    async def makemigrations_from_diff(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate migration from schema differences."""
        diff = await self.generator._compare_schemas(old_schema, new_schema)
        migration = await self.generator.generate_migration_from_diff(diff, description, author)
        
        filepath = self.generator.save_migration(migration)
        return migration
    
    async def makemigrations_initial(
        self,
        models: List[Any],
        description: str = "Initial migration",
        author: Optional[str] = None
    ) -> Migration:
        """Generate initial migration from models."""
        migration = await self.generator.generate_migration_from_current_schema(
            models, description, author
        )
        
        filepath = self.generator.save_migration(migration)
        return migration
    
    # ============================================================================
    # MIGRATION EXECUTION
    # ============================================================================
    
    async def migrate(
        self,
        target_version: Optional[str] = None,
        dry_run: bool = False,
        force: bool = False,
        use_transaction: Optional[bool] = None
    ) -> MigrationExecutionResult:
        """Run migrations up to a target version."""
        # Determine execution mode
        if dry_run:
            mode = MigrationExecutionMode.DRY_RUN
        elif force:
            mode = MigrationExecutionMode.FORCE
        elif use_transaction or (use_transaction is None and self.config.use_transactions):
            mode = MigrationExecutionMode.TRANSACTION
        else:
            mode = MigrationExecutionMode.NORMAL
        
        # Validate migration plan if configured
        if self.config.validate_before_run and not dry_run:
            validation = await self.runner.validate_migration_plan(target_version)
            if not validation['is_valid']:
                raise ValueError(f"Migration plan validation failed: {validation}")
        
        # Execute migrations
        result = await self.runner.run_migrations(target_version, mode)
        
        return result
    
    async def migrate_rollback(
        self,
        target_version: str,
        dry_run: bool = False,
        force: bool = False,
        use_transaction: Optional[bool] = None
    ) -> MigrationExecutionResult:
        """Rollback migrations to a target version."""
        # Determine execution mode
        if dry_run:
            mode = MigrationExecutionMode.DRY_RUN
        elif force:
            mode = MigrationExecutionMode.FORCE
        elif use_transaction or (use_transaction is None and self.config.use_transactions):
            mode = MigrationExecutionMode.TRANSACTION
        else:
            mode = MigrationExecutionMode.NORMAL
        
        # Check rollback depth
        if not force:
            applied_migrations = await self.runner._get_applied_migrations()
            rollback_count = len(self.runner._get_migrations_to_rollback(applied_migrations, target_version))
            
            if rollback_count > self.config.max_rollback_depth:
                raise ValueError(
                    f"Rollback would affect {rollback_count} migrations, "
                    f"exceeding maximum depth of {self.config.max_rollback_depth}. "
                    f"Use --force to override."
                )
        
        # Execute rollback
        result = await self.runner.rollback_migrations(target_version, mode)
        
        return result
    
    # ============================================================================
    # MIGRATION MANAGEMENT
    # ============================================================================
    
    async def showmigrations(self, limit: int = 10) -> Dict[str, Any]:
        """Show migration status and history."""
        status = await self.runner.get_migration_status()
        history = await self.runner.get_migration_history(limit)
        
        return {
            'status': status,
            'history': history
        }
    
    async def showmigrations_plan(
        self,
        target_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Show what migrations would be executed."""
        pending_migrations = await self.runner._get_pending_migrations()
        
        if target_version:
            pending_migrations = self.runner._filter_migrations_to_target(pending_migrations, target_version)
        
        dependency_plan = self.runner._resolve_dependencies(pending_migrations)
        
        return {
            'migrations_to_run': [
                {
                    'version': m.version,
                    'name': m.name,
                    'description': m.description,
                    'dependencies': m.dependencies
                }
                for m in pending_migrations
            ],
            'dependency_plan': dependency_plan.get_summary(),
            'total_count': len(pending_migrations)
        }
    
    async def showmigrations_rollback_plan(self, target_version: str) -> Dict[str, Any]:
        """Show what migrations would be rolled back."""
        applied_migrations = await self.runner._get_applied_migrations()
        rollback_migrations = self.runner._get_migrations_to_rollback(applied_migrations, target_version)
        
        return {
            'migrations_to_rollback': [
                {
                    'version': m.version,
                    'name': m.name,
                    'description': m.description
                }
                for m in rollback_migrations
            ],
            'total_count': len(rollback_migrations)
        }
    
    # ============================================================================
    # SCHEMA MANAGEMENT
    # ============================================================================
    
    async def get_current_schema(self) -> Dict[str, Any]:
        """Get current database schema."""
        return await self.generator.schema_inspector.get_schema()
    
    async def compare_schemas(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> SchemaDiff:
        """Compare two schemas and return differences."""
        return await self.generator._compare_schemas(old_schema, new_schema)
    
    async def generate_schema_sql(
        self,
        models: List[Any],
        database_type: Optional[str] = None
    ) -> str:
        """Generate SQL to create schema from models."""
        model_schema = await self.generator._extract_schema_from_models(models)
        
        # Create a diff from empty schema to model schema
        empty_schema = {}
        diff = await self.generator._compare_schemas(empty_schema, model_schema)
        
        # Generate SQL
        changes = self.generator._diff_to_changes(diff)
        sql = await self.generator._generate_up_sql(changes)
        
        return sql
    
    # ============================================================================
    # MULTI-DATABASE SUPPORT
    # ============================================================================
    
    def add_database(
        self,
        name: str,
        engine,
        config: Optional[MigrationConfig] = None
    ):
        """Add a database for multi-database migrations."""
        config = config or self.config
        self.database_engines[name] = {
            'engine': engine,
            'config': config,
            'generator': EnhancedMigrationGenerator(engine, config.migrations_dir),
            'runner': EnhancedMigrationRunner(engine, config.migrations_dir)
        }
    
    def switch_database(self, name: str):
        """Switch to a different database."""
        if name not in self.database_engines:
            raise ValueError(f"Database '{name}' not found")
        
        self.current_database = name
        db_config = self.database_engines[name]
        
        # Update current engine and components
        self.engine = db_config['engine']
        self.config = db_config['config']
        self.generator = db_config['generator']
        self.runner = db_config['runner']
    
    async def migrate_all_databases(
        self,
        target_version: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, MigrationExecutionResult]:
        """Run migrations on all databases."""
        results = {}
        
        for db_name in self.database_engines:
            self.switch_database(db_name)
            results[db_name] = await self.migrate(target_version, dry_run)
        
        return results
    
    # ============================================================================
    # MIGRATION VALIDATION AND SAFETY
    # ============================================================================
    
    async def validate_migration(
        self,
        migration: Union[Migration, str]
    ) -> Dict[str, Any]:
        """Validate a migration file or object."""
        if isinstance(migration, str):
            # Load migration from file
            migration = self.generator.load_migration(migration)
        
        return await self.generator.validate_migration(migration)
    
    async def validate_all_migrations(self) -> Dict[str, Any]:
        """Validate all migration files."""
        migration_files = self.generator.list_migration_files()
        results = {}
        
        for filepath in migration_files:
            try:
                migration = self.generator.load_migration(filepath)
                validation = await self.generator.validate_migration(migration)
                results[filepath] = validation
            except Exception as e:
                results[filepath] = {
                    'is_valid': False,
                    'errors': [str(e)],
                    'warnings': []
                }
        
        return results
    
    async def check_migration_safety(
        self,
        migration: Union[Migration, str]
    ) -> Dict[str, Any]:
        """Check migration for potentially dangerous operations."""
        if isinstance(migration, str):
            migration = self.generator.load_migration(migration)
        
        safety_check = {
            'is_safe': True,
            'warnings': [],
            'dangerous_operations': []
        }
        
        # Check for dangerous SQL keywords
        dangerous_keywords = [
            'DROP TABLE', 'DROP DATABASE', 'TRUNCATE', 'DELETE FROM'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in migration.up_sql.upper():
                safety_check['dangerous_operations'].append(keyword)
                if keyword not in self.config.allowed_dangerous_operations:
                    safety_check['is_safe'] = False
                    safety_check['warnings'].append(f"Dangerous operation: {keyword}")
        
        # Check for data loss operations
        if 'DROP COLUMN' in migration.up_sql.upper():
            safety_check['warnings'].append("Operation may cause data loss: DROP COLUMN")
        
        return safety_check
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def list_migrations(self) -> List[str]:
        """List all migration files."""
        return self.generator.list_migration_files()
    
    def get_migration_by_version(self, version: str) -> Optional[Migration]:
        """Get migration by version."""
        migration_files = self.generator.list_migration_files()
        
        for filepath in migration_files:
            try:
                migration = self.generator.load_migration(filepath)
                if migration.version == version:
                    return migration
            except Exception:
                continue
        
        return None
    
    async def create_migration_template(
        self,
        template_name: str,
        up_sql: str,
        down_sql: str,
        variables: List[str]
    ):
        """Create a custom migration template."""
        # This would extend the template system
        # Implementation depends on how you want to store custom templates
        pass
    
    async def backup_database(self, backup_path: str):
        """Create a database backup before migration."""
        if not self.config.backup_before_migration:
            return
        
        # Implementation depends on database type
        # This is a placeholder for database-specific backup logic
        pass
    
    async def restore_database(self, backup_path: str):
        """Restore database from backup."""
        # Implementation depends on database type
        # This is a placeholder for database-specific restore logic
        pass 