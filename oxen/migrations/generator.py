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
            table_name = getattr(model, '_meta', {}).table_name or model.__name__.lower()
            sql_parts.append(f"-- Create table: {table_name}")
            
            # Get model fields
            fields = []
            if hasattr(model, '_meta') and hasattr(model._meta, 'fields_map'):
                for field_name, field_obj in model._meta.fields_map.items():
                    if field_name != 'id':  # Skip the default ID field
                        field_sql = self._generate_field_sql(field_name, field_obj)
                        if field_sql:  # Only add non-None field SQL
                            fields.append(field_sql)
            
            # Add default ID field if not present
            if not any('id' in field.lower() for field in fields):
                fields.insert(0, "id INTEGER PRIMARY KEY AUTOINCREMENT")
            else:
                # Ensure the ID field has proper constraints
                id_field_index = next((i for i, field in enumerate(fields) if 'id' in field.lower()), None)
                if id_field_index is not None:
                    # Replace the ID field with proper constraints
                    fields[id_field_index] = "id INTEGER PRIMARY KEY AUTOINCREMENT"
            
            # Add timestamp fields (only if not already present)
            if not any('created_at' in field.lower() for field in fields):
                fields.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            if not any('updated_at' in field.lower() for field in fields):
                fields.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            sql_parts.append(f"CREATE TABLE {table_name} (")
            sql_parts.append("    " + ",\n    ".join(fields))
            sql_parts.append(");")
            sql_parts.append("")
        
        return "\n".join(sql_parts)
    
    def _generate_field_sql(self, field_name: str, field_obj: Any) -> str:
        """Generate SQL for a specific field."""
        # Skip ManyToMany fields as they don't create columns in the main table
        if field_obj.__class__.__name__ == 'ManyToManyField':
            return None
        
        field_type = self._get_field_type(field_obj)
        constraints = self._get_field_constraints(field_obj)
        
        sql_parts = [f"{field_name} {field_type}"]
        sql_parts.extend(constraints)
        
        return " ".join(sql_parts)
    
    def _get_field_type(self, field_obj: Any) -> str:
        """Get the SQL type for a field."""
        field_class = field_obj.__class__.__name__
        
        type_mapping = {
            'CharField': 'VARCHAR',
            'TextField': 'TEXT',
            'IntField': 'INTEGER',
            'IntegerField': 'INTEGER',
            'FloatField': 'REAL',
            'DecimalField': 'DECIMAL',
            'BooleanField': 'BOOLEAN',
            'DateTimeField': 'TIMESTAMP',
            'DateField': 'DATE',
            'TimeField': 'TIME',
            'UUIDField': 'VARCHAR',
            'JSONField': 'TEXT',
            'BinaryField': 'BLOB',
            'EmailField': 'VARCHAR',
            'URLField': 'VARCHAR',
            'SlugField': 'VARCHAR',
            'FileField': 'VARCHAR',
            'ImageField': 'VARCHAR',
            'ArrayField': 'TEXT',
            'RangeField': 'TEXT',
            'HStoreField': 'TEXT',
            'JSONBField': 'TEXT',
            'ForeignKeyField': 'INTEGER',
            'OneToOneField': 'INTEGER',
            'ManyToManyField': 'TEXT',  # ManyToMany doesn't have a direct column
        }
        
        base_type = type_mapping.get(field_class, 'TEXT')
        
        # Add length for VARCHAR fields
        if base_type == 'VARCHAR':
            max_length = getattr(field_obj, 'max_length', 255)
            return f"VARCHAR({max_length})"
        
        # Add precision for DECIMAL fields
        if base_type == 'DECIMAL':
            max_digits = getattr(field_obj, 'max_digits', 10)
            decimal_places = getattr(field_obj, 'decimal_places', 2)
            return f"DECIMAL({max_digits},{decimal_places})"
        
        return base_type
    
    def _get_field_constraints(self, field_obj: Any) -> List[str]:
        """Get constraints for a field."""
        constraints = []
        
        # Primary key
        if getattr(field_obj, 'primary_key', False):
            constraints.append("PRIMARY KEY")
        
        # Auto increment
        if getattr(field_obj, 'auto_increment', False):
            constraints.append("AUTOINCREMENT")
        
        # Not null
        if not getattr(field_obj, 'null', True):
            constraints.append("NOT NULL")
        
        # Unique
        if getattr(field_obj, 'unique', False):
            constraints.append("UNIQUE")
        
        # Default value
        default = getattr(field_obj, 'default', None)
        if default is not None and default != '':
            if callable(default):
                # Handle callable defaults (like lambda functions)
                # For DateTimeField with auto_now_add, use CURRENT_TIMESTAMP
                if hasattr(field_obj, 'auto_now_add') and field_obj.auto_now_add:
                    constraints.append("DEFAULT CURRENT_TIMESTAMP")
                elif hasattr(field_obj, 'auto_now') and field_obj.auto_now:
                    constraints.append("DEFAULT CURRENT_TIMESTAMP")
                else:
                    # For other callable defaults, try to evaluate them
                    try:
                        evaluated_default = default()
                        if isinstance(evaluated_default, str):
                            escaped_default = evaluated_default.replace("'", "''")
                            constraints.append(f"DEFAULT \"{escaped_default}\"")
                        else:
                            constraints.append(f"DEFAULT {evaluated_default}")
                    except:
                        # If we can't evaluate it, skip the default
                        pass
            elif isinstance(default, str):
                # Escape single quotes in string defaults and ensure proper quoting
                escaped_default = default.replace("'", "''")
                # Use double quotes for string defaults to avoid comment issues
                constraints.append(f"DEFAULT \"{escaped_default}\"")
            else:
                constraints.append(f"DEFAULT {default}")
        
        return constraints
    
    def _generate_drop_tables_sql(self, models: List[Any]) -> str:
        """Generate DROP TABLE SQL from models."""
        sql_parts = []
        
        for model in reversed(models):  # Drop in reverse order for foreign key constraints
            table_name = getattr(model, '_meta', {}).table_name or model.__name__.lower()
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