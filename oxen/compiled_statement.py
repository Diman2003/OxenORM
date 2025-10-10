"""
CompiledStatement API for OxenORM
Defines the CompiledStatement struct and related row factories.
"""
from typing import Any, Callable, List, Dict, Optional

class CompiledStatement:
    def __init__(self, sql: str, param_types: List[Any], result_shape: List[str], row_factory: Callable, cache_key: str):
        self.sql = sql
        self.param_types = param_types
        self.result_shape = result_shape
        self.row_factory = row_factory
        self.cache_key = cache_key

# Row Factories
class TuplesFactory:
    def __call__(self, rows):
        return [tuple(row) for row in rows]

class ModelsFactory:
    def __init__(self, model_cls):
        self.model_cls = model_cls
    def __call__(self, rows):
        return [self.model_cls(**row) for row in rows]

class DictFactory:
    def __call__(self, rows):
        return [dict(row) for row in rows]

class ArrowFactory:
    def __call__(self, rows):
        # Placeholder for zero-copy Arrow materialization
        import pyarrow as pa
        return pa.Table.from_pylist(rows)

ROW_FACTORIES = {
    'tuple': TuplesFactory(),
    'model': ModelsFactory,
    'dict': DictFactory(),
    'arrow': ArrowFactory(),
}
