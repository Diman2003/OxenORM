import asyncio
import json

import pytest

from oxen.rust_engine import OxenEngine, RUST_AVAILABLE


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not built")
def test_generate_ddl_from_diff_create_table_sqlite_memory():
    async def _run():
        eng = OxenEngine("sqlite::memory:")
        await eng.connect()

        old_schema = {"tables": []}
        new_schema = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "data_type": "INTEGER", "nullable": False},
                        {"name": "name", "data_type": "TEXT", "nullable": True},
                    ],
                }
            ]
        }

        ddl = await eng.generate_ddl_from_diff(old_schema, new_schema)
        assert "CREATE TABLE" in ddl.get("up_sql", "")
        assert "users" in ddl.get("up_sql", "")
        assert "DROP TABLE" in ddl.get("down_sql", "")
    asyncio.run(_run())


