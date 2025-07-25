"""
Migration data models and enums.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


class MigrationStatus(Enum):
    """Migration status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Represents a database migration."""
    
    # Migration identification
    id: str
    name: str
    version: str
    
    # Migration content
    up_sql: str
    down_sql: str
    
    # Metadata
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Execution tracking
    status: MigrationStatus = MigrationStatus.PENDING
    executed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    
    # Dependencies
    dependencies: List[str] = None  # List of migration IDs this depends on
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert migration to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'up_sql': self.up_sql,
            'down_sql': self.down_sql,
            'description': self.description,
            'author': self.author,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status.value,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'execution_time_ms': self.execution_time_ms,
            'error_message': self.error_message,
            'dependencies': self.dependencies
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Migration':
        """Create migration from dictionary."""
        # Parse datetime fields
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        executed_at = None
        if data.get('executed_at'):
            executed_at = datetime.fromisoformat(data['executed_at'])
        
        return cls(
            id=data['id'],
            name=data['name'],
            version=data['version'],
            up_sql=data['up_sql'],
            down_sql=data['down_sql'],
            description=data.get('description'),
            author=data.get('author'),
            created_at=created_at,
            status=MigrationStatus(data.get('status', 'pending')),
            executed_at=executed_at,
            execution_time_ms=data.get('execution_time_ms'),
            error_message=data.get('error_message'),
            dependencies=data.get('dependencies', [])
        )


@dataclass
class MigrationPlan:
    """Represents a plan for migration execution."""
    
    migrations_to_run: List[Migration]
    migrations_to_rollback: List[Migration]
    dependencies_resolved: bool = False
    conflicts: List[str] = None  # List of conflict descriptions
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []
    
    def is_valid(self) -> bool:
        """Check if the migration plan is valid."""
        return len(self.conflicts) == 0 and self.dependencies_resolved
    
    def add_conflict(self, conflict: str):
        """Add a conflict to the plan."""
        self.conflicts.append(conflict)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the migration plan."""
        return {
            'migrations_to_run': len(self.migrations_to_run),
            'migrations_to_rollback': len(self.migrations_to_rollback),
            'is_valid': self.is_valid(),
            'conflicts': self.conflicts,
            'dependencies_resolved': self.dependencies_resolved
        }


@dataclass
class SchemaDiff:
    """Represents differences between two database schemas."""
    
    tables_added: List[str] = None
    tables_removed: List[str] = None
    tables_modified: List[str] = None
    
    columns_added: Dict[str, List[str]] = None  # table_name -> [column_names]
    columns_removed: Dict[str, List[str]] = None
    columns_modified: Dict[str, List[str]] = None
    
    indexes_added: Dict[str, List[str]] = None  # table_name -> [index_names]
    indexes_removed: Dict[str, List[str]] = None
    
    constraints_added: Dict[str, List[str]] = None  # table_name -> [constraint_names]
    constraints_removed: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.tables_added is None:
            self.tables_added = []
        if self.tables_removed is None:
            self.tables_removed = []
        if self.tables_modified is None:
            self.tables_modified = []
        if self.columns_added is None:
            self.columns_added = {}
        if self.columns_removed is None:
            self.columns_removed = {}
        if self.columns_modified is None:
            self.columns_modified = {}
        if self.indexes_added is None:
            self.indexes_added = {}
        if self.indexes_removed is None:
            self.indexes_removed = {}
        if self.constraints_added is None:
            self.constraints_added = {}
        if self.constraints_removed is None:
            self.constraints_removed = {}
    
    def has_changes(self) -> bool:
        """Check if there are any changes in the diff."""
        return (
            len(self.tables_added) > 0 or
            len(self.tables_removed) > 0 or
            len(self.tables_modified) > 0 or
            any(len(cols) > 0 for cols in self.columns_added.values()) or
            any(len(cols) > 0 for cols in self.columns_removed.values()) or
            any(len(cols) > 0 for cols in self.columns_modified.values()) or
            any(len(idxs) > 0 for idxs in self.indexes_added.values()) or
            any(len(idxs) > 0 for idxs in self.indexes_removed.values()) or
            any(len(cons) > 0 for cons in self.constraints_added.values()) or
            any(len(cons) > 0 for cons in self.constraints_removed.values())
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the schema differences."""
        return {
            'tables_added': len(self.tables_added),
            'tables_removed': len(self.tables_removed),
            'tables_modified': len(self.tables_modified),
            'total_columns_added': sum(len(cols) for cols in self.columns_added.values()),
            'total_columns_removed': sum(len(cols) for cols in self.columns_removed.values()),
            'total_columns_modified': sum(len(cols) for cols in self.columns_modified.values()),
            'total_indexes_added': sum(len(idxs) for idxs in self.indexes_added.values()),
            'total_indexes_removed': sum(len(idxs) for idxs in self.indexes_removed.values()),
            'total_constraints_added': sum(len(cons) for cons in self.constraints_added.values()),
            'total_constraints_removed': sum(len(cons) for cons in self.constraints_removed.values()),
            'has_changes': self.has_changes()
        } 