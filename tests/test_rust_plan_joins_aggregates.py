#!/usr/bin/env python3
import asyncio
from oxen.rust_engine import OxenEngine


def test_rust_plan_joins_and_aggregates_sqlite_memory():
    async def _run():
        eng = OxenEngine("sqlite::memory:")
        await eng.connect()
        await eng.execute_query(
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
        )
        await eng.execute_query(
            "CREATE TABLE posts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT)"
        )
        await eng.execute_query("INSERT INTO users (name) VALUES (?)", ["u1"])
        await eng.execute_query("INSERT INTO users (name) VALUES (?)", ["u2"])
        await eng.execute_query("INSERT INTO posts (user_id, title) VALUES (?, ?)", [1, "p1"])
        await eng.execute_query("INSERT INTO posts (user_id, title) VALUES (?, ?)", [1, "p2"])
        await eng.execute_query("INSERT INTO posts (user_id, title) VALUES (?, ?)", [2, "p3"])

        # Join query
        plan = {
            "table": "posts",
            "select": ["posts.id", "posts.title", "users.name"],
            "joins": [
                {
                    "join_type": "inner",
                    "table": "users",
                    "on_left": "posts.user_id",
                    "on_right": "users.id",
                }
            ],
            "order_by": [{"field": "posts.id", "direction": "asc"}],
        }
        res = await eng.execute_plan(plan)
        assert res.get("error") is None
        data = res.get("data")
        assert len(data) == 3
        assert data[0]["title"] == "p1" and data[0]["name"] == "u1"

        # Aggregation
        plan2 = {
            "table": "posts",
            "aggregates": [{"func": "count", "field": "posts.id", "alias": "cnt"}],
            "group_by": ["posts.user_id"],
            "joins": [
                {
                    "join_type": "inner",
                    "table": "users",
                    "on_left": "posts.user_id",
                    "on_right": "users.id",
                }
            ],
            "order_by": [{"field": "posts.user_id", "direction": "asc"}],
        }
        res2 = await eng.execute_plan(plan2)
        assert res2.get("error") is None
        data2 = res2.get("data")
        # u1 has 2 posts, u2 has 1
        cnts = [row["cnt"] for row in data2]
        assert cnts == [2, 1]

    asyncio.run(_run())


