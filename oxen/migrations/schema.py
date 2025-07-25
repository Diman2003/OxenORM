"""
Schema inspection and diff generation for migrations.
"""

import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from .models import SchemaDiff


@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    columns: Dict[str, 'ColumnInfo']
    indexes: Dict[str, 'IndexInfo']
    constraints: Dict[str, 'ConstraintInfo']
    comment: Optional[str] = None


@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_unique: bool = False
    comment: Optional[str] = None


@dataclass
class IndexInfo:
    """Information about a database index."""
    name: str
    table_name: str
    columns: List[str]
    is_unique: bool
    index_type: str = "btree"


@dataclass
class ConstraintInfo:
    """Information about a database constraint."""
    name: str
    table_name: str
    constraint_type: str  # PRIMARY_KEY, FOREIGN_KEY, UNIQUE, CHECK, NOT_NULL
    columns: List[str]
    definition: Optional[str] = None


class SchemaInspector:
    """Inspects database schema and generates diffs."""
    
    def __init__(self, engine):
        self.engine = engine
    
    async def get_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        result = await self.engine.execute_query(sql)
        return [row['table_name'] for row in result['data']]
    
    async def get_table_info(self, table_name: str) -> TableInfo:
        """Get detailed information about a specific table."""
        # Get columns
        columns_sql = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = $1
        ORDER BY ordinal_position
        """
        
        columns_result = await self.engine.execute_query(columns_sql, [table_name])
        columns = {}
        
        for row in columns_result['data']:
            column_name = row['column_name']
            columns[column_name] = ColumnInfo(
                name=column_name,
                data_type=row['data_type'],
                is_nullable=row['is_nullable'] == 'YES',
                default_value=row['column_default']
            )
        
        # Get indexes
        indexes_sql = """
        SELECT 
            i.relname as index_name,
            array_to_string(array_agg(a.attname), ',') as column_names,
            ix.indisunique as is_unique,
            am.amname as index_type
        FROM pg_index ix
        JOIN pg_class t ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_am am ON am.oid = i.relam
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        WHERE t.relname = $1
        AND t.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        GROUP BY i.relname, ix.indisunique, am.amname
        ORDER BY i.relname
        """
        
        indexes_result = await self.engine.execute_query(indexes_sql, [table_name])
        indexes = {}
        
        for row in indexes_result['data']:
            index_name = row['index_name']
            column_names = row['column_names'].split(',')
            indexes[index_name] = IndexInfo(
                name=index_name,
                table_name=table_name,
                columns=column_names,
                is_unique=row['is_unique'],
                index_type=row['index_type']
            )
        
        # Get constraints
        constraints_sql = """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            array_to_string(array_agg(kcu.column_name), ',') as column_names,
            cc.check_clause
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        LEFT JOIN information_schema.check_constraints cc 
            ON tc.constraint_name = cc.constraint_name
        WHERE tc.table_schema = 'public' 
        AND tc.table_name = $1
        GROUP BY tc.constraint_name, tc.constraint_type, cc.check_clause
        ORDER BY tc.constraint_name
        """
        
        constraints_result = await self.engine.execute_query(constraints_sql, [table_name])
        constraints = {}
        
        for row in constraints_result['data']:
            constraint_name = row['constraint_name']
            column_names = row['column_names'].split(',') if row['column_names'] else []
            constraints[constraint_name] = ConstraintInfo(
                name=constraint_name,
                table_name=table_name,
                constraint_type=row['constraint_type'],
                columns=column_names,
                definition=row.get('check_clause')
            )
        
        return TableInfo(
            name=table_name,
            columns=columns,
            indexes=indexes,
            constraints=constraints
        )
    
    async def get_schema(self) -> Dict[str, TableInfo]:
        """Get complete database schema."""
        tables = await self.get_tables()
        schema = {}
        
        for table_name in tables:
            schema[table_name] = await self.get_table_info(table_name)
        
        return schema
    
    def compare_schemas(self, old_schema: Dict[str, TableInfo], new_schema: Dict[str, TableInfo]) -> SchemaDiff:
        """Compare two schemas and generate a diff."""
        diff = SchemaDiff()
        
        old_tables = set(old_schema.keys())
        new_tables = set(new_schema.keys())
        
        # Tables added/removed
        diff.tables_added = list(new_tables - old_tables)
        diff.tables_removed = list(old_tables - new_tables)
        diff.tables_modified = list(old_tables & new_tables)
        
        # Compare modified tables
        for table_name in diff.tables_modified:
            old_table = old_schema[table_name]
            new_table = new_schema[table_name]
            
            # Compare columns
            old_columns = set(old_table.columns.keys())
            new_columns = set(new_table.columns.keys())
            
            columns_added = new_columns - old_columns
            columns_removed = old_columns - new_columns
            columns_modified = old_columns & new_columns
            
            if columns_added:
                diff.columns_added[table_name] = list(columns_added)
            if columns_removed:
                diff.columns_removed[table_name] = list(columns_removed)
            
            # Check for modified columns
            modified_cols = []
            for col_name in columns_modified:
                old_col = old_table.columns[col_name]
                new_col = new_table.columns[col_name]
                
                if (old_col.data_type != new_col.data_type or
                    old_col.is_nullable != new_col.is_nullable or
                    old_col.default_value != new_col.default_value):
                    modified_cols.append(col_name)
            
            if modified_cols:
                diff.columns_modified[table_name] = modified_cols
            
            # Compare indexes
            old_indexes = set(old_table.indexes.keys())
            new_indexes = set(new_table.indexes.keys())
            
            indexes_added = new_indexes - old_indexes
            indexes_removed = old_indexes - new_indexes
            
            if indexes_added:
                diff.indexes_added[table_name] = list(indexes_added)
            if indexes_removed:
                diff.indexes_removed[table_name] = list(indexes_removed)
            
            # Compare constraints
            old_constraints = set(old_table.constraints.keys())
            new_constraints = set(new_table.constraints.keys())
            
            constraints_added = new_constraints - old_constraints
            constraints_removed = old_constraints - new_constraints
            
            if constraints_added:
                diff.constraints_added[table_name] = list(constraints_added)
            if constraints_removed:
                diff.constraints_removed[table_name] = list(constraints_removed)
        
        return diff
    
    def generate_migration_sql(self, diff: SchemaDiff, direction: str = "up") -> str:
        """Generate SQL for a migration based on schema diff."""
        sql_parts = []
        
        if direction == "up":
            # Add tables
            for table_name in diff.tables_added:
                sql_parts.append(f"-- Add table: {table_name}")
                # This would need the full table definition from the new schema
                sql_parts.append(f"CREATE TABLE {table_name} ();")
                sql_parts.append("")
            
            # Add columns
            for table_name, columns in diff.columns_added.items():
                for column_name in columns:
                    sql_parts.append(f"-- Add column {column_name} to {table_name}")
                    sql_parts.append(f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(255);")
                    sql_parts.append("")
            
            # Add indexes
            for table_name, indexes in diff.indexes_added.items():
                for index_name in indexes:
                    sql_parts.append(f"-- Add index {index_name} to {table_name}")
                    sql_parts.append(f"CREATE INDEX {index_name} ON {table_name} ();")
                    sql_parts.append("")
            
            # Add constraints
            for table_name, constraints in diff.constraints_added.items():
                for constraint_name in constraints:
                    sql_parts.append(f"-- Add constraint {constraint_name} to {table_name}")
                    sql_parts.append(f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} ();")
                    sql_parts.append("")
        
        elif direction == "down":
            # Remove constraints
            for table_name, constraints in diff.constraints_added.items():
                for constraint_name in constraints:
                    sql_parts.append(f"-- Remove constraint {constraint_name} from {table_name}")
                    sql_parts.append(f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name};")
                    sql_parts.append("")
            
            # Remove indexes
            for table_name, indexes in diff.indexes_added.items():
                for index_name in indexes:
                    sql_parts.append(f"-- Remove index {index_name} from {table_name}")
                    sql_parts.append(f"DROP INDEX {index_name};")
                    sql_parts.append("")
            
            # Remove columns
            for table_name, columns in diff.columns_added.items():
                for column_name in columns:
                    sql_parts.append(f"-- Remove column {column_name} from {table_name}")
                    sql_parts.append(f"ALTER TABLE {table_name} DROP COLUMN {column_name};")
                    sql_parts.append("")
            
            # Remove tables
            for table_name in diff.tables_added:
                sql_parts.append(f"-- Remove table: {table_name}")
                sql_parts.append(f"DROP TABLE {table_name};")
                sql_parts.append("")
        
        return "\n".join(sql_parts) 