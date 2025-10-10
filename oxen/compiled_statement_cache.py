"""
Global LRU cache for compiled statements in OxenORM
"""
from collections import OrderedDict
from datetime import datetime, timedelta
from oxen.compiled_statement import CompiledStatement

class CompiledStatementCache:
    def __init__(self, max_size: int = 256):
        self.max_size = max_size
        self.cache: OrderedDict[str, CompiledStatement] = OrderedDict()
        self.metadata: dict = {}

    def get(self, cache_key: str) -> CompiledStatement:
        if cache_key in self.cache:
            self.cache.move_to_end(cache_key)
            return self.cache[cache_key]
        return None

    def set(self, cache_key: str, statement: CompiledStatement):
        if cache_key in self.cache:
            self.cache.move_to_end(cache_key)
        elif len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[cache_key] = statement
        self.metadata[cache_key] = {
            'result_shape': statement.result_shape,
            'row_factory': statement.row_factory,
            'created_at': datetime.now()
        }

    def prewarm(self, compiler_cls, common_irs):
        """Prewarm cache by compiling common IRs."""
        for ir in common_irs:
            compiler = compiler_cls(ir)
            sql, params, param_types, cache_key = compiler.compile()
            stmt = CompiledStatement(sql, param_types, ir.columns, None, cache_key)
            self.set(cache_key, stmt)

    def get_metadata(self, cache_key: str):
        return self.metadata.get(cache_key)

    def clear(self):
        self.cache.clear()
        self.metadata.clear()
