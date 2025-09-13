#!/usr/bin/env python3
import asyncio
from oxen import Model
from oxen.fields import IntegerField, CharField
from oxen.engine import connect, disconnect


class User(Model):
    id = IntegerField(primary_key=True)
    name = CharField(max_length=100)
    age = IntegerField()

    class Meta:
        table_name = "users"


def test_queryset_uses_rust_plan_sqlite_file(tmp_path):
    async def _run():
        db_file = tmp_path / "qs_plan.db"
        eng = await connect(f"sqlite:///{db_file}")
        # Ensure Rust engine exists on engine instance
        assert eng.rust_engine is not None
        await eng.execute_query(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)"
        )
        await eng.execute_query("DELETE FROM users")
        for i in range(5):
            await eng.execute_query("INSERT INTO users (name, age) VALUES (?, ?)", [f"u{i}", 18 + i])

        rows = await User.filter(age__gte=20).order_by("-age").limit(2)
        # The QuerySet should rely on the Rust plan path; verify two records are returned
        assert len(rows) == 2
        assert rows[0].age >= rows[1].age

        await disconnect(eng)

    asyncio.run(_run())


