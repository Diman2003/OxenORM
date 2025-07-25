"""
Migration generation utilities.
"""

import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import Migration, MigrationStatus
from .schema import SchemaInspector, SchemaDiff


class MigrationGenerator:
    """Generates new migrations based on schema changes."""
    
    def __init__(self, engine, migrations_dir: str = "migrations"):
        self.engine = engine
        self.migrations_dir = migrations_dir
        self.schema_inspector = SchemaInspector(engine)
        
        # Ensure migrations directory exists
        os.makedirs(migrations_dir, exist_ok=True)
    
    def generate_migration_id(self) -> str:
        """Generate a unique migration ID."""
        return str(uuid.uuid4())
    
    def generate_migration_name(self, description: str) -> str:
        """Generate a migration name from description."""
        # Convert description to snake_case
        name = description.lower().replace(' ', '_').replace('-', '_')
        # Remove special characters
        name = ''.join(c for c in name if c.isalnum() or c == '_')
        # Add timestamp with milliseconds
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:20]  # Include milliseconds
        return f"{timestamp}_{name}"
    
    async def create_migration_from_diff(
        self, 
        description: str,
        up_sql: str,
        down_sql: str,
        author: Optional[str] = None
    ) -> Migration:
        """Create a new migration from SQL statements."""
        
        migration_id = self.generate_migration_id()
        migration_name = self.generate_migration_name(description)
        
        migration = Migration(
            id=migration_id,
            name=migration_name,
            version=datetime.now().strftime("%Y%m%d%H%M%S%f")[:17],  # Include milliseconds
            up_sql=up_sql,
            down_sql=down_sql,
            description=description,
            author=author,
            created_at=datetime.utcnow()
        )
        
        return migration
    
    async def generate_migration_from_schema_diff(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate a migration from schema differences."""
        
        # Convert schemas to TableInfo objects
        old_table_infos = {}
        new_table_infos = {}
        
        # This is a simplified version - in practice, you'd need to convert
        # the schema dictionaries to proper TableInfo objects
        
        # Generate diff
        diff = self.schema_inspector.compare_schemas(old_table_infos, new_table_infos)
        
        # Generate SQL
        up_sql = self.schema_inspector.generate_migration_sql(diff, "up")
        down_sql = self.schema_inspector.generate_migration_sql(diff, "down")
        
        return await self.create_migration_from_diff(description, up_sql, down_sql, author)
    
    async def generate_migration_from_models(
        self,
        models: List[Any],  # List of model classes
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate a migration from model definitions."""
        
        # This would analyze model classes and generate SQL
        # For now, we'll create a placeholder migration
        
        up_sql = self._generate_create_tables_sql(models)
        down_sql = self._generate_drop_tables_sql(models)
        
        return await self.create_migration_from_diff(description, up_sql, down_sql, author)
    
    def _generate_create_tables_sql(self, models: List[Any]) -> str:
        """Generate CREATE TABLE SQL from models."""
        sql_parts = []
        
        for model in models:
            table_name = getattr(model, '__tablename__', model.__name__.lower())
            sql_parts.append(f"-- Create table: {table_name}")
            sql_parts.append(f"CREATE TABLE {table_name} (")
            sql_parts.append("    id SERIAL PRIMARY KEY,")
            sql_parts.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
            sql_parts.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            sql_parts.append(");")
            sql_parts.append("")
        
        return "\n".join(sql_parts)
    
    def _generate_drop_tables_sql(self, models: List[Any]) -> str:
        """Generate DROP TABLE SQL from models."""
        sql_parts = []
        
        for model in reversed(models):  # Drop in reverse order for foreign key constraints
            table_name = getattr(model, '__tablename__', model.__name__.lower())
            sql_parts.append(f"-- Drop table: {table_name}")
            sql_parts.append(f"DROP TABLE IF EXISTS {table_name};")
            sql_parts.append("")
        
        return "\n".join(sql_parts)
    
    def save_migration(self, migration: Migration) -> str:
        """Save migration to file system."""
        filename = f"{migration.version}_{migration.name}.py"
        filepath = os.path.join(self.migrations_dir, filename)
        
        content = self._generate_migration_file_content(migration)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        return filepath
    
    def _generate_migration_file_content(self, migration: Migration) -> str:
        """Generate Python file content for a migration."""
        return f'''"""
Migration: {migration.name}

{migration.description or 'No description provided'}

Generated on: {migration.created_at.isoformat() if migration.created_at else 'Unknown'}
Author: {migration.author or 'Unknown'}
"""

from oxen.migrations import Migration, MigrationStatus


def up():
    """Apply the migration."""
    return Migration(
        id="{migration.id}",
        name="{migration.name}",
        version="{migration.version}",
        up_sql="""{migration.up_sql}""",
        down_sql="""{migration.down_sql}""",
        description="{migration.description or ''}",
        author="{migration.author or ''}",
        status=MigrationStatus.PENDING
    )


def down():
    """Rollback the migration."""
    return Migration(
        id="{migration.id}",
        name="{migration.name}",
        version="{migration.version}",
        up_sql="""{migration.up_sql}""",
        down_sql="""{migration.down_sql}""",
        description="{migration.description or ''}",
        author="{migration.author or ''}",
        status=MigrationStatus.PENDING
    )
'''
    
    def load_migration_from_file(self, filepath: str) -> Migration:
        """Load migration from file."""
        import importlib.util
        
        # Load the migration module
        spec = importlib.util.spec_from_file_location("migration", filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the migration
        return module.up()
    
    def list_migrations(self) -> List[str]:
        """List all migration files."""
        if not os.path.exists(self.migrations_dir):
            return []
        
        migrations = []
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                migrations.append(os.path.join(self.migrations_dir, filename))
        
        return sorted(migrations)
    
    def get_migration_by_version(self, version: str) -> Optional[Migration]:
        """Get migration by version."""
        for filepath in self.list_migrations():
            migration = self.load_migration_from_file(filepath)
            if migration.version == version:
                return migration
        return None 