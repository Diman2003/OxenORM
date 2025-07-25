"""
Main migration engine for OxenORM.
"""

from typing import List, Dict, Any, Optional
from .models import Migration, MigrationStatus, MigrationPlan, SchemaDiff
from .generator import MigrationGenerator
from .runner import MigrationRunner
from .schema import SchemaInspector


class MigrationEngine:
    """Main migration engine that coordinates all migration operations."""
    
    def __init__(self, engine, migrations_dir: str = "migrations"):
        self.engine = engine
        self.migrations_dir = migrations_dir
        self.generator = MigrationGenerator(engine, migrations_dir)
        self.runner = MigrationRunner(engine, migrations_dir)
        self.schema_inspector = SchemaInspector(engine)
    
    async def create_migration(
        self, 
        description: str,
        up_sql: str,
        down_sql: str,
        author: Optional[str] = None
    ) -> Migration:
        """Create a new migration."""
        migration = await self.generator.create_migration_from_diff(
            description, up_sql, down_sql, author
        )
        
        # Save to file system
        filepath = self.generator.save_migration(migration)
        
        return migration
    
    async def generate_migration_from_schema_diff(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate a migration from schema differences."""
        migration = await self.generator.generate_migration_from_schema_diff(
            old_schema, new_schema, description, author
        )
        
        # Save to file system
        filepath = self.generator.save_migration(migration)
        
        return migration
    
    async def generate_migration_from_models(
        self,
        models: List[Any],
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate a migration from model definitions."""
        migration = await self.generator.generate_migration_from_models(
            models, description, author
        )
        
        # Save to file system
        filepath = self.generator.save_migration(migration)
        
        return migration
    
    async def run_migrations(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """Run migrations up to a target version."""
        # Ensure migrations table exists
        await self.runner._ensure_migrations_table()
        return await self.runner.run_migrations(target_version)
    
    async def rollback_migrations(self, target_version: str) -> Dict[str, Any]:
        """Rollback migrations to a target version."""
        # Ensure migrations table exists
        await self.runner._ensure_migrations_table()
        return await self.runner.rollback_migrations(target_version)
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        # Ensure migrations table exists
        await self.runner._ensure_migrations_table()
        return await self.runner.get_migration_status()
    
    async def get_applied_migrations(self) -> List[Migration]:
        """Get list of applied migrations."""
        # Ensure migrations table exists
        await self.runner._ensure_migrations_table()
        return await self.runner.get_applied_migrations()
    
    async def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        # Ensure migrations table exists
        await self.runner._ensure_migrations_table()
        return await self.runner.get_pending_migrations()
    
    async def create_migration_plan(self, target_version: Optional[str] = None) -> MigrationPlan:
        """Create a migration plan."""
        return await self.runner.create_migration_plan(target_version)
    
    async def get_current_schema(self) -> Dict[str, Any]:
        """Get current database schema."""
        return await self.schema_inspector.get_schema()
    
    async def compare_schemas(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> SchemaDiff:
        """Compare two schemas and generate a diff."""
        return self.schema_inspector.compare_schemas(old_schema, new_schema)
    
    async def generate_migration_sql(self, diff: SchemaDiff, direction: str = "up") -> str:
        """Generate SQL for a migration based on schema diff."""
        return self.schema_inspector.generate_migration_sql(diff, direction)
    
    def list_migrations(self) -> List[str]:
        """List all migration files."""
        return self.generator.list_migrations()
    
    def get_migration_by_version(self, version: str) -> Optional[Migration]:
        """Get migration by version."""
        return self.generator.get_migration_by_version(version)
    
    async def validate_migration(self, migration: Migration) -> Dict[str, Any]:
        """Validate a migration before running it."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if migration has required fields
        if not migration.up_sql.strip():
            validation_result['valid'] = False
            validation_result['errors'].append("Migration must have up_sql")
        
        if not migration.down_sql.strip():
            validation_result['warnings'].append("Migration has no down_sql (cannot be rolled back)")
        
        # Check SQL syntax (basic validation)
        if not self._validate_sql_syntax(migration.up_sql):
            validation_result['warnings'].append("Up SQL may have syntax issues")
        
        if migration.down_sql and not self._validate_sql_syntax(migration.down_sql):
            validation_result['warnings'].append("Down SQL may have syntax issues")
        
        # Check dependencies
        for dep_version in migration.dependencies:
            dep_migration = self.get_migration_by_version(dep_version)
            if not dep_migration:
                validation_result['errors'].append(f"Dependency migration {dep_version} not found")
                validation_result['valid'] = False
        
        return validation_result
    
    def _validate_sql_syntax(self, sql: str) -> bool:
        """Basic SQL syntax validation."""
        # This is a very basic validation - in practice, you'd want more sophisticated parsing
        sql = sql.strip().upper()
        
        # Check for basic SQL keywords
        if not any(keyword in sql for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']):
            return False
        
        # Check for balanced parentheses
        if sql.count('(') != sql.count(')'):
            return False
        
        # Check for balanced quotes
        single_quotes = sql.count("'")
        double_quotes = sql.count('"')
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            return False
        
        return True
    
    async def dry_run_migration(self, migration: Migration) -> Dict[str, Any]:
        """Perform a dry run of a migration without executing it."""
        # This would analyze the migration and show what would happen
        # For now, we'll just validate it
        validation = await self.validate_migration(migration)
        
        return {
            'migration': migration,
            'validation': validation,
            'sql_preview': {
                'up_sql': migration.up_sql,
                'down_sql': migration.down_sql
            },
            'estimated_impact': self._estimate_migration_impact(migration)
        }
    
    def _estimate_migration_impact(self, migration: Migration) -> Dict[str, Any]:
        """Estimate the impact of a migration."""
        impact = {
            'tables_affected': [],
            'operations': [],
            'risk_level': 'low'
        }
        
        sql = migration.up_sql.upper()
        
        # Detect table operations
        if 'CREATE TABLE' in sql:
            impact['operations'].append('create_table')
            impact['risk_level'] = 'low'
        
        if 'DROP TABLE' in sql:
            impact['operations'].append('drop_table')
            impact['risk_level'] = 'high'
        
        if 'ALTER TABLE' in sql:
            impact['operations'].append('alter_table')
            impact['risk_level'] = 'medium'
        
        if 'INSERT' in sql:
            impact['operations'].append('insert_data')
            impact['risk_level'] = 'low'
        
        if 'DELETE' in sql:
            impact['operations'].append('delete_data')
            impact['risk_level'] = 'high'
        
        return impact
    
    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get detailed migration history."""
        applied_migrations = await self.get_applied_migrations()
        history = []
        
        for migration in applied_migrations:
            history.append({
                'version': migration.version,
                'name': migration.name,
                'description': migration.description,
                'status': migration.status.value,
                'executed_at': migration.executed_at.isoformat() if migration.executed_at else None,
                'execution_time_ms': migration.execution_time_ms,
                'author': migration.author,
                'error_message': migration.error_message
            })
        
        return history 