#!/usr/bin/env python3
import asyncio
from oxen.rust_engine import OxenEngine


def test_rust_plan_basic_sqlite_memory():
    async def _run():
        eng = OxenEngine("sqlite::memory:")
        await eng.connect()
        await eng.execute_query(
            "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, v INTEGER)"
        )
        for i in range(5):
            await eng.execute_query("INSERT INTO t (v) VALUES (?)", [i])

        plan = {
            "table": "t",
            "select": ["id", "v"],
            "filters": [{"field": "v", "op": "gte", "value": 2}],
            "order_by": [{"field": "v", "direction": "desc"}],
            "limit": 2,
            "offset": 0,
        }
        res = await eng.execute_plan(plan)
        assert res.get("error") is None
        data = res.get("data")
        assert isinstance(data, list)
        assert len(data) == 2
        # should be highest first: v=4, v=3
        vs = [row["v"] for row in data]
        assert vs == [4, 3]

    asyncio.run(_run())


