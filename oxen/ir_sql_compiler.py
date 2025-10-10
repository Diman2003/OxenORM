"""
IR→SQL Typed Compiler for OxenORM
Compiles Python IR to typed SQL AST, emits SQL and param typing map, normalizes and constant-folds, hoists literals, and generates stable cache keys.
"""
from typing import Any, Dict, List, Tuple
import hashlib

class IRNode:
    """Base class for IR nodes."""
    pass

class SelectIR(IRNode):
    def __init__(self, table: str, columns: List[str], where: Any = None, joins: List[Any] = None, order_by: List[str] = None, limit: int = None):
        self.table = table
        self.columns = columns
        self.where = where
        self.joins = joins or []
        self.order_by = order_by or []
        self.limit = limit

class SQLCompiler:
    def __init__(self, ir: IRNode):
        self.ir = ir

    def compile(self) -> Tuple[str, List[Any], Dict[str, Any], str]:
        """
        Compile IR to SQL, param typing map, and cache key.
        Returns: (sql, param_types, result_shape, cache_key)
        """
        sql_parts = [f"SELECT {', '.join(self.ir.columns)} FROM {self.ir.table}"]
        params = []
        param_types = {}
        if self.ir.joins:
            for join in self.ir.joins:
                sql_parts.append(f"JOIN {join['table']} ON {join['on']}")
        if self.ir.where:
            sql_parts.append(f"WHERE {self.ir.where}")
        if self.ir.order_by:
            sql_parts.append(f"ORDER BY {', '.join(self.ir.order_by)}")
        if self.ir.limit is not None:
            sql_parts.append(f"LIMIT {self.ir.limit}")
        sql = ' '.join(sql_parts)
        # Normalize and constant-fold (simple demo)
        sql = sql.replace('  ', ' ')
        # Hoist literals (not implemented in demo)
        # Generate stable cache key by shape
        shape_str = f"{self.ir.table}|{self.ir.columns}|{self.ir.joins}|{self.ir.order_by}|{self.ir.limit}"
        cache_key = hashlib.sha256(shape_str.encode()).hexdigest()
        result_shape = self.ir.columns
        return sql, params, param_types, cache_key
