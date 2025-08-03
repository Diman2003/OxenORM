#!/usr/bin/env python3
"""
Admin Interface for OxenORM

This module provides an admin interface for schema visualization,
model management, and database administration.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class SchemaObjectType(Enum):
    """Types of schema objects."""
    TABLE = "table"
    COLUMN = "column"
    INDEX = "index"
    CONSTRAINT = "constraint"
    RELATIONSHIP = "relationship"


class RelationshipType(Enum):
    """Types of relationships."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


@dataclass
class SchemaColumn:
    """Represents a database column."""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    default: Optional[str] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    auto_increment: bool = False
    foreign_key: Optional[str] = None
    description: Optional[str] = None


@dataclass
class SchemaIndex:
    """Represents a database index."""
    name: str
    columns: List[str]
    unique: bool = False
    type: str = "BTREE"  # Default index type


@dataclass
class SchemaConstraint:
    """Represents a database constraint."""
    name: str
    type: str  # PRIMARY_KEY, FOREIGN_KEY, UNIQUE, CHECK, etc.
    columns: List[str]
    referenced_table: Optional[str] = None
    referenced_columns: Optional[List[str]] = None
    on_delete: Optional[str] = None
    on_update: Optional[str] = None


@dataclass
class SchemaRelationship:
    """Represents a relationship between tables."""
    name: str
    source_table: str
    target_table: str
    relationship_type: RelationshipType
    source_column: str
    target_column: str
    through_table: Optional[str] = None
    cascade_delete: bool = False
    cascade_update: bool = False


@dataclass
class SchemaTable:
    """Represents a database table."""
    name: str
    columns: List[SchemaColumn] = field(default_factory=list)
    indexes: List[SchemaIndex] = field(default_factory=list)
    constraints: List[SchemaConstraint] = field(default_factory=list)
    relationships: List[SchemaRelationship] = field(default_factory=list)
    description: Optional[str] = None
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None


@dataclass
class SchemaDiagram:
    """Represents a database schema diagram."""
    tables: List[SchemaTable] = field(default_factory=list)
    relationships: List[SchemaRelationship] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SchemaAnalyzer:
    """Analyzes database schema and generates visualizations."""
    
    def __init__(self):
        self.tables: Dict[str, SchemaTable] = {}
        self.relationships: List[SchemaRelationship] = []
    
    def analyze_schema_from_models(self, models: List[Any]) -> SchemaDiagram:
        """Analyze schema from model classes."""
        diagram = SchemaDiagram()
        
        for model in models:
            table = self._extract_table_from_model(model)
            diagram.tables.append(table)
            self.tables[table.name] = table
        
        # Analyze relationships
        self._analyze_relationships(models)
        diagram.relationships = self.relationships
        
        return diagram
    
    def _extract_table_from_model(self, model_class: Any) -> SchemaTable:
        """Extract table information from a model class."""
        table = SchemaTable(name=model_class._meta.table_name)
        
        # Extract columns from model fields
        for field_name, field_obj in model_class._meta.fields_map.items():
            column = self._extract_column_from_field(field_name, field_obj)
            table.columns.append(column)
        
        # Extract indexes and constraints
        self._extract_indexes_and_constraints(model_class, table)
        
        return table
    
    def _extract_column_from_field(self, field_name: str, field_obj: Any) -> SchemaColumn:
        """Extract column information from a model field."""
        column = SchemaColumn(
            name=field_name,
            data_type=self._get_field_data_type(field_obj),
            nullable=not getattr(field_obj, 'null', False),
            primary_key=getattr(field_obj, 'primary_key', False),
            unique=getattr(field_obj, 'unique', False),
            default=str(getattr(field_obj, 'default', None)) if getattr(field_obj, 'default') is not None else None,
            max_length=getattr(field_obj, 'max_length', None),
            auto_increment=getattr(field_obj, 'auto_increment', False),
            description=getattr(field_obj, 'help_text', None)
        )
        
        return column
    
    def _get_field_data_type(self, field_obj: Any) -> str:
        """Get the database data type for a field."""
        field_type = type(field_obj).__name__.lower()
        
        type_mapping = {
            'charfield': 'VARCHAR',
            'textfield': 'TEXT',
            'integerfield': 'INTEGER',
            'intfield': 'INTEGER',
            'floatfield': 'FLOAT',
            'decimalfield': 'DECIMAL',
            'booleanfield': 'BOOLEAN',
            'datetimefield': 'DATETIME',
            'datefield': 'DATE',
            'timefield': 'TIME',
            'uuidfield': 'UUID',
            'jsonfield': 'JSON',
            'binaryfield': 'BLOB',
            'emailfield': 'VARCHAR',
            'urlfield': 'VARCHAR',
            'slugfield': 'VARCHAR',
            'filefield': 'VARCHAR',
            'imagefield': 'VARCHAR',
            'arrayfield': 'TEXT',
            'rangefield': 'TEXT',
            'hstorefield': 'HSTORE',
            'jsonbfield': 'JSONB',
            'geometryfield': 'GEOMETRY',
            'foreignkeyfield': 'INTEGER',
            'onetoonfield': 'INTEGER',
            'manytomanyfield': 'INTEGER'
        }
        
        return type_mapping.get(field_type, 'TEXT')
    
    def _extract_indexes_and_constraints(self, model_class: Any, table: SchemaTable):
        """Extract indexes and constraints from a model."""
        # Add primary key constraint
        pk_columns = [col.name for col in table.columns if col.primary_key]
        if pk_columns:
            table.constraints.append(SchemaConstraint(
                name=f"pk_{table.name}",
                type="PRIMARY_KEY",
                columns=pk_columns
            ))
        
        # Add unique constraints
        unique_columns = [col.name for col in table.columns if col.unique and not col.primary_key]
        for col in unique_columns:
            table.constraints.append(SchemaConstraint(
                name=f"uq_{table.name}_{col}",
                type="UNIQUE",
                columns=[col]
            ))
        
        # Add foreign key constraints
        for col in table.columns:
            if col.foreign_key:
                table.constraints.append(SchemaConstraint(
                    name=f"fk_{table.name}_{col.name}",
                    type="FOREIGN_KEY",
                    columns=[col.name],
                    referenced_table=col.foreign_key,
                    referenced_columns=['id']
                ))
    
    def _analyze_relationships(self, models: List[Any]):
        """Analyze relationships between models."""
        for model in models:
            for field_name, field_obj in model._meta.fields_map.items():
                if hasattr(field_obj, 'is_relational') and field_obj.is_relational:
                    relationship = self._extract_relationship(model, field_name, field_obj)
                    if relationship:
                        self.relationships.append(relationship)
    
    def _extract_relationship(self, model: Any, field_name: str, field_obj: Any) -> Optional[SchemaRelationship]:
        """Extract relationship information from a field."""
        related_model = field_obj._get_related_model()
        
        if not related_model:
            return None
        
        # Determine relationship type
        if hasattr(field_obj, 'unique') and field_obj.unique:
            relationship_type = RelationshipType.ONE_TO_ONE
        elif hasattr(field_obj, 'through') and field_obj.through:
            relationship_type = RelationshipType.MANY_TO_MANY
        else:
            relationship_type = RelationshipType.ONE_TO_MANY
        
        return SchemaRelationship(
            name=f"{model._meta.table_name}_{field_name}",
            source_table=model._meta.table_name,
            target_table=related_model._meta.table_name,
            relationship_type=relationship_type,
            source_column=field_name,
            target_column='id',
            through_table=getattr(field_obj, 'through', None)
        )


class AdminInterface:
    """Main admin interface for database management."""
    
    def __init__(self):
        self.schema_analyzer = SchemaAnalyzer()
        self.models: List[Any] = []
        self.diagram: Optional[SchemaDiagram] = None
    
    def register_models(self, models: List[Any]):
        """Register models for admin interface."""
        self.models = models
        self.diagram = self.schema_analyzer.analyze_schema_from_models(models)
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a summary of the database schema."""
        if not self.diagram:
            return {}
        
        total_columns = sum(len(table.columns) for table in self.diagram.tables)
        total_indexes = sum(len(table.indexes) for table in self.diagram.tables)
        total_constraints = sum(len(table.constraints) for table in self.diagram.tables)
        
        return {
            'tables_count': len(self.diagram.tables),
            'columns_count': total_columns,
            'indexes_count': total_indexes,
            'constraints_count': total_constraints,
            'relationships_count': len(self.diagram.relationships),
            'tables': [
                {
                    'name': table.name,
                    'columns_count': len(table.columns),
                    'indexes_count': len(table.indexes),
                    'constraints_count': len(table.constraints),
                    'row_count': table.row_count,
                    'size_bytes': table.size_bytes
                }
                for table in self.diagram.tables
            ]
        }
    
    def get_table_details(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific table."""
        if not self.diagram:
            return None
        
        for table in self.diagram.tables:
            if table.name == table_name:
                return {
                    'name': table.name,
                    'description': table.description,
                    'columns': [
                        {
                            'name': col.name,
                            'data_type': col.data_type,
                            'nullable': col.nullable,
                            'primary_key': col.primary_key,
                            'unique': col.unique,
                            'default': col.default,
                            'max_length': col.max_length,
                            'auto_increment': col.auto_increment,
                            'description': col.description
                        }
                        for col in table.columns
                    ],
                    'indexes': [
                        {
                            'name': idx.name,
                            'columns': idx.columns,
                            'unique': idx.unique,
                            'type': idx.type
                        }
                        for idx in table.indexes
                    ],
                    'constraints': [
                        {
                            'name': const.name,
                            'type': const.type,
                            'columns': const.columns,
                            'referenced_table': const.referenced_table,
                            'referenced_columns': const.referenced_columns
                        }
                        for const in table.constraints
                    ],
                    'relationships': [
                        {
                            'name': rel.name,
                            'target_table': rel.target_table,
                            'relationship_type': rel.relationship_type.value,
                            'source_column': rel.source_column,
                            'target_column': rel.target_column
                        }
                        for rel in self.diagram.relationships
                        if rel.source_table == table_name
                    ]
                }
        
        return None
    
    def generate_schema_diagram(self) -> Dict[str, Any]:
        """Generate a schema diagram for visualization."""
        if not self.diagram:
            return {}
        
        # Generate nodes for tables
        nodes = []
        for table in self.diagram.tables:
            node = {
                'id': table.name,
                'type': 'table',
                'label': table.name,
                'data': {
                    'columns': len(table.columns),
                    'indexes': len(table.indexes),
                    'constraints': len(table.constraints)
                }
            }
            nodes.append(node)
        
        # Generate edges for relationships
        edges = []
        for relationship in self.diagram.relationships:
            edge = {
                'id': relationship.name,
                'source': relationship.source_table,
                'target': relationship.target_table,
                'type': relationship.relationship_type.value,
                'data': {
                    'source_column': relationship.source_column,
                    'target_column': relationship.target_column
                }
            }
            edges.append(edge)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'total_tables': len(nodes),
                'total_relationships': len(edges),
                'generated_at': datetime.now().isoformat()
            }
        }
    
    def export_schema_json(self, filename: str):
        """Export schema diagram to JSON file."""
        if not self.diagram:
            return
        
        data = {
            'schema': self.generate_schema_diagram(),
            'summary': self.get_schema_summary(),
            'tables': [
                self.get_table_details(table.name)
                for table in self.diagram.tables
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def generate_sql_ddl(self) -> Dict[str, str]:
        """Generate SQL DDL statements for all tables."""
        if not self.diagram:
            return {}
        
        ddl_statements = {}
        
        for table in self.diagram.tables:
            ddl = self._generate_table_ddl(table)
            ddl_statements[table.name] = ddl
        
        return ddl_statements
    
    def _generate_table_ddl(self, table: SchemaTable) -> str:
        """Generate SQL DDL for a specific table."""
        lines = [f"CREATE TABLE {table.name} ("]
        
        # Add columns
        column_definitions = []
        for column in table.columns:
            col_def = f"    {column.name} {column.data_type}"
            
            if column.max_length:
                col_def += f"({column.max_length})"
            elif column.precision and column.scale:
                col_def += f"({column.precision},{column.scale})"
            
            if not column.nullable:
                col_def += " NOT NULL"
            
            if column.primary_key:
                col_def += " PRIMARY KEY"
            
            if column.unique and not column.primary_key:
                col_def += " UNIQUE"
            
            if column.auto_increment:
                col_def += " AUTO_INCREMENT"
            
            if column.default is not None:
                col_def += f" DEFAULT {column.default}"
            
            column_definitions.append(col_def)
        
        lines.append(",\n".join(column_definitions))
        
        # Add constraints
        for constraint in table.constraints:
            if constraint.type == "PRIMARY_KEY" and len(constraint.columns) > 1:
                lines.append(f",\n    PRIMARY KEY ({', '.join(constraint.columns)})")
            elif constraint.type == "UNIQUE":
                lines.append(f",\n    UNIQUE ({', '.join(constraint.columns)})")
            elif constraint.type == "FOREIGN_KEY":
                lines.append(f",\n    FOREIGN KEY ({', '.join(constraint.columns)}) "
                           f"REFERENCES {constraint.referenced_table}({', '.join(constraint.referenced_columns or ['id'])})")
        
        lines.append(");")
        
        return "\n".join(lines)


# Global admin interface instance
_global_admin = AdminInterface()


def get_admin() -> AdminInterface:
    """Get the global admin interface instance."""
    return _global_admin


def register_models_for_admin(models: List[Any]):
    """Register models with the global admin interface."""
    _global_admin.register_models(models)


def get_schema_summary() -> Dict[str, Any]:
    """Get schema summary from global admin interface."""
    return _global_admin.get_schema_summary()


def export_schema_json(filename: str):
    """Export schema to JSON file."""
    _global_admin.export_schema_json(filename) 