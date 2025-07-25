#!/usr/bin/env python3
"""
Enhanced Migration Generator for OxenORM

This module provides advanced migration generation capabilities including:
- Automatic migration generation from model changes
- Complex schema operations (add/remove columns, indexes, constraints)
- Multi-database support
- Schema diffing and comparison
- Migration templates and customization
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .models import Migration, SchemaDiff
from .schema import SchemaInspector


class MigrationType(Enum):
    """Types of migrations that can be generated."""
    CREATE_TABLE = "create_table"
    DROP_TABLE = "drop_table"
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    MODIFY_COLUMN = "modify_column"
    ADD_INDEX = "add_index"
    DROP_INDEX = "drop_index"
    ADD_CONSTRAINT = "add_constraint"
    DROP_CONSTRAINT = "drop_constraint"
    RENAME_TABLE = "rename_table"
    RENAME_COLUMN = "rename_column"
    DATA_MIGRATION = "data_migration"
    CUSTOM_SQL = "custom_sql"


@dataclass
class SchemaChange:
    """Represents a single schema change."""
    change_type: MigrationType
    table_name: str
    column_name: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    sql_up: Optional[str] = None
    sql_down: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationTemplate:
    """Template for generating migration SQL."""
    name: str
    description: str
    up_template: str
    down_template: str
    variables: List[str] = field(default_factory=list)
    database_specific: Dict[str, str] = field(default_factory=dict)


class EnhancedMigrationGenerator:
    """Enhanced migration generator with advanced features."""
    
    def __init__(self, engine, migrations_dir: str = "migrations"):
        self.engine = engine
        self.migrations_dir = migrations_dir
        self.schema_inspector = SchemaInspector(engine)
        self.templates = self._load_migration_templates()
        
        # Ensure migrations directory exists
        os.makedirs(migrations_dir, exist_ok=True)
    
    def _load_migration_templates(self) -> Dict[str, MigrationTemplate]:
        """Load migration templates for different operations."""
        templates = {}
        
        # Create table template
        templates['create_table'] = MigrationTemplate(
            name="Create Table",
            description="Create a new table",
            up_template="""
CREATE TABLE {table_name} (
    {columns}
);
""",
            down_template="DROP TABLE {table_name};",
            variables=['table_name', 'columns']
        )
        
        # Add column template
        templates['add_column'] = MigrationTemplate(
            name="Add Column",
            description="Add a new column to a table",
            up_template="ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};",
            down_template="ALTER TABLE {table_name} DROP COLUMN {column_name};",
            variables=['table_name', 'column_name', 'column_type']
        )
        
        # Drop column template
        templates['drop_column'] = MigrationTemplate(
            name="Drop Column",
            description="Remove a column from a table",
            up_template="ALTER TABLE {table_name} DROP COLUMN {column_name};",
            down_template="ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};",
            variables=['table_name', 'column_name', 'column_type']
        )
        
        # Modify column template
        templates['modify_column'] = MigrationTemplate(
            name="Modify Column",
            description="Modify an existing column",
            up_template="ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type};",
            down_template="ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {old_type};",
            variables=['table_name', 'column_name', 'new_type', 'old_type']
        )
        
        # Add index template
        templates['add_index'] = MigrationTemplate(
            name="Add Index",
            description="Add an index to a table",
            up_template="CREATE INDEX {index_name} ON {table_name} ({columns});",
            down_template="DROP INDEX {index_name};",
            variables=['index_name', 'table_name', 'columns']
        )
        
        # Add constraint template
        templates['add_constraint'] = MigrationTemplate(
            name="Add Constraint",
            description="Add a constraint to a table",
            up_template="ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} {constraint_definition};",
            down_template="ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name};",
            variables=['table_name', 'constraint_name', 'constraint_definition']
        )
        
        return templates
    
    async def generate_migration_from_models(
        self,
        old_models: List[Any],
        new_models: List[Any],
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate migration from model changes."""
        # Extract schemas from models
        old_schema = await self._extract_schema_from_models(old_models)
        new_schema = await self._extract_schema_from_models(new_models)
        
        # Generate schema diff
        diff = await self._compare_schemas(old_schema, new_schema)
        
        # Generate migration from diff
        return await self.generate_migration_from_diff(diff, description, author)
    
    async def generate_migration_from_diff(
        self,
        diff: SchemaDiff,
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate migration from schema differences."""
        # Convert diff to schema changes
        changes = self._diff_to_changes(diff)
        
        # Generate SQL for changes
        up_sql = await self._generate_up_sql(changes)
        down_sql = await self._generate_down_sql(changes)
        
        # Create migration
        migration_id = self._generate_migration_id(description)
        version = self._generate_version()
        
        migration = Migration(
            id=migration_id,
            name=f"{version}_{description.lower().replace(' ', '_')}",
            version=version,
            up_sql=up_sql,
            down_sql=down_sql,
            description=description,
            author=author,
            created_at=datetime.utcnow()
        )
        
        return migration
    
    async def generate_migration_from_current_schema(
        self,
        models: List[Any],
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate initial migration from current models."""
        # Get current database schema
        current_schema = await self.schema_inspector.get_schema()
        
        # Extract schema from models
        model_schema = await self._extract_schema_from_models(models)
        
        # Create diff (empty current schema vs model schema)
        diff = SchemaDiff()
        diff.tables_added = list(model_schema.keys())
        diff.columns_added = {
            table: list(schema.keys()) 
            for table, schema in model_schema.items()
        }
        
        return await self.generate_migration_from_diff(diff, description, author)
    
    async def generate_data_migration(
        self,
        up_sql: str,
        down_sql: str,
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate a data migration."""
        migration_id = self._generate_migration_id(description)
        version = self._generate_version()
        
        migration = Migration(
            id=migration_id,
            name=f"{version}_{description.lower().replace(' ', '_')}",
            version=version,
            up_sql=up_sql,
            down_sql=down_sql,
            description=description,
            author=author,
            created_at=datetime.utcnow()
        )
        
        return migration
    
    async def generate_rollback_migration(
        self,
        target_migration: Migration,
        description: str,
        author: Optional[str] = None
    ) -> Migration:
        """Generate a rollback migration for a specific migration."""
        migration_id = self._generate_migration_id(f"rollback_{target_migration.version}")
        version = self._generate_version()
        
        # Swap up and down SQL for rollback
        migration = Migration(
            id=migration_id,
            name=f"{version}_rollback_{target_migration.version}",
            version=version,
            up_sql=target_migration.down_sql,
            down_sql=target_migration.up_sql,
            description=description,
            author=author,
            created_at=datetime.utcnow()
        )
        
        return migration
    
    def save_migration(self, migration: Migration) -> str:
        """Save migration to file system."""
        filename = f"{migration.version}_{migration.name}.json"
        filepath = os.path.join(self.migrations_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(migration.to_dict(), f, indent=2)
        
        return filepath
    
    def load_migration(self, filepath: str) -> Migration:
        """Load migration from file system."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return Migration.from_dict(data)
    
    def list_migration_files(self) -> List[str]:
        """List all migration files in the migrations directory."""
        if not os.path.exists(self.migrations_dir):
            return []
        
        files = []
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.json'):
                files.append(os.path.join(self.migrations_dir, filename))
        
        return sorted(files)
    
    async def _extract_schema_from_models(self, models: List[Any]) -> Dict[str, Dict[str, Any]]:
        """Extract schema information from model classes."""
        schema = {}
        
        for model in models:
            if hasattr(model, '_meta'):
                table_name = model._meta.table_name
                schema[table_name] = {}
                
                for field_name, field_obj in model._meta.fields.items():
                    schema[table_name][field_name] = {
                        'type': field_obj.field_type,
                        'nullable': field_obj.nullable,
                        'default': field_obj.default,
                        'primary_key': field_obj.primary_key,
                        'unique': field_obj.unique,
                        'index': field_obj.index,
                        'foreign_key': field_obj.foreign_key,
                        'max_length': getattr(field_obj, 'max_length', None),
                        'precision': getattr(field_obj, 'precision', None),
                        'scale': getattr(field_obj, 'scale', None),
                    }
        
        return schema
    
    async def _compare_schemas(
        self, 
        old_schema: Dict[str, Dict[str, Any]], 
        new_schema: Dict[str, Dict[str, Any]]
    ) -> SchemaDiff:
        """Compare two schemas and generate differences."""
        diff = SchemaDiff()
        
        # Compare tables
        old_tables = set(old_schema.keys())
        new_tables = set(new_schema.keys())
        
        diff.tables_added = list(new_tables - old_tables)
        diff.tables_removed = list(old_tables - new_tables)
        diff.tables_modified = list(old_tables & new_tables)
        
        # Compare columns for modified tables
        for table in diff.tables_modified:
            old_columns = set(old_schema[table].keys())
            new_columns = set(new_schema[table].keys())
            
            added_columns = new_columns - old_columns
            removed_columns = old_columns - new_columns
            modified_columns = []
            
            # Check for modified columns
            for col in old_columns & new_columns:
                if old_schema[table][col] != new_schema[table][col]:
                    modified_columns.append(col)
            
            if added_columns:
                diff.columns_added[table] = list(added_columns)
            if removed_columns:
                diff.columns_removed[table] = list(removed_columns)
            if modified_columns:
                diff.columns_modified[table] = modified_columns
        
        return diff
    
    def _diff_to_changes(self, diff: SchemaDiff) -> List[SchemaChange]:
        """Convert schema diff to list of schema changes."""
        changes = []
        
        # Handle table additions
        for table in diff.tables_added:
            changes.append(SchemaChange(
                change_type=MigrationType.CREATE_TABLE,
                table_name=table
            ))
        
        # Handle table removals
        for table in diff.tables_removed:
            changes.append(SchemaChange(
                change_type=MigrationType.DROP_TABLE,
                table_name=table
            ))
        
        # Handle column changes
        for table, columns in diff.columns_added.items():
            for column in columns:
                changes.append(SchemaChange(
                    change_type=MigrationType.ADD_COLUMN,
                    table_name=table,
                    column_name=column
                ))
        
        for table, columns in diff.columns_removed.items():
            for column in columns:
                changes.append(SchemaChange(
                    change_type=MigrationType.DROP_COLUMN,
                    table_name=table,
                    column_name=column
                ))
        
        for table, columns in diff.columns_modified.items():
            for column in columns:
                changes.append(SchemaChange(
                    change_type=MigrationType.MODIFY_COLUMN,
                    table_name=table,
                    column_name=column
                ))
        
        return changes
    
    async def _generate_up_sql(self, changes: List[SchemaChange]) -> str:
        """Generate UP migration SQL from schema changes."""
        sql_parts = []
        
        for change in changes:
            if change.sql_up:
                sql_parts.append(change.sql_up)
            else:
                sql_parts.append(self._generate_sql_for_change(change, "up"))
        
        return "\n".join(sql_parts)
    
    async def _generate_down_sql(self, changes: List[SchemaChange]) -> str:
        """Generate DOWN migration SQL from schema changes."""
        # Reverse the changes for rollback
        reversed_changes = list(reversed(changes))
        sql_parts = []
        
        for change in reversed_changes:
            if change.sql_down:
                sql_parts.append(change.sql_down)
            else:
                sql_parts.append(self._generate_sql_for_change(change, "down"))
        
        return "\n".join(sql_parts)
    
    def _generate_sql_for_change(self, change: SchemaChange, direction: str) -> str:
        """Generate SQL for a specific schema change."""
        template_name = f"{change.change_type.value}"
        template = self.templates.get(template_name)
        
        if not template:
            return f"-- TODO: Generate SQL for {change.change_type.value}"
        
        # Get template based on direction
        template_sql = template.up_template if direction == "up" else template.down_template
        
        # Replace variables in template
        sql = template_sql
        for var in template.variables:
            value = getattr(change, var, None)
            if value is not None:
                sql = sql.replace(f"{{{var}}}", str(value))
        
        return sql
    
    def _generate_migration_id(self, description: str) -> str:
        """Generate a unique migration ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hash_input = f"{description}_{timestamp}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"{timestamp}_{hash_value}"
    
    def _generate_version(self) -> str:
        """Generate a migration version string."""
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    async def validate_migration(self, migration: Migration) -> Dict[str, Any]:
        """Validate a migration for correctness and safety."""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Check for empty SQL
        if not migration.up_sql.strip():
            validation_result['errors'].append("UP migration SQL is empty")
            validation_result['is_valid'] = False
        
        if not migration.down_sql.strip():
            validation_result['warnings'].append("DOWN migration SQL is empty - rollback may not be possible")
        
        # Check for dangerous operations
        dangerous_keywords = ['DROP TABLE', 'DROP DATABASE', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in migration.up_sql.upper():
                validation_result['warnings'].append(f"Migration contains potentially dangerous operation: {keyword}")
        
        # Check for syntax issues (basic)
        if ';' not in migration.up_sql:
            validation_result['warnings'].append("UP migration may be missing semicolons")
        
        return validation_result 