#!/usr/bin/env python3
import asyncio
from oxen.rust_engine import OxenEngine


def test_introspection_sqlite_memory():
    async def _run():
        eng = OxenEngine("sqlite::memory:")
        await eng.connect()
        await eng.execute_query(
            "CREATE TABLE x (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)"
        )
        schema = await eng.introspect_schema()
        # Convert PyObject to dict by str->json
        assert schema is not None

    asyncio.run(_run())


def test_introspection_postgres_url_parsing_smoke(monkeypatch):
    # Smoke test: ensure wrapper can be constructed and has method; no real connection.
    import asyncio
    from oxen.rust_engine import OxenEngine, RUST_AVAILABLE

    if not RUST_AVAILABLE:
        return

    async def _run():
        eng = OxenEngine("postgresql://user:pass@localhost:5432/db")
        assert hasattr(eng, 'introspect_schema')

    asyncio.run(_run())


def test_introspection_mysql_url_parsing_smoke(monkeypatch):
    import asyncio
    from oxen.rust_engine import OxenEngine, RUST_AVAILABLE

    if not RUST_AVAILABLE:
        return

    async def _run():
        eng = OxenEngine("mysql://user:pass@localhost:3306/db")
        assert hasattr(eng, 'introspect_schema')

    asyncio.run(_run())


