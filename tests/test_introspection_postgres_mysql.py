import os
import asyncio
import pytest

from oxen.rust_engine import OxenEngine, RUST_AVAILABLE


pytestmark = pytest.mark.integration


POSTGRES_URL = os.environ.get("OXEN_PG_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
MYSQL_URL = os.environ.get("OXEN_MYSQL_URL", "mysql://root:password@localhost:3306/mysql")


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not built")
def test_live_postgres_introspection_connect_and_inspect():
    async def _run():
        eng = OxenEngine(POSTGRES_URL)
        try:
            await eng.connect()
        except Exception as e:
            pytest.skip(f"Cannot connect to Postgres at {POSTGRES_URL}: {e}")
        schema = await eng.introspect_schema()
        assert isinstance(schema, dict)
        assert 'tables' in schema
    asyncio.run(_run())


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust engine not built")
def test_live_mysql_introspection_connect_and_inspect():
    async def _run():
        eng = OxenEngine(MYSQL_URL)
        try:
            await eng.connect()
        except Exception as e:
            pytest.skip(f"Cannot connect to MySQL at {MYSQL_URL}: {e}")
        schema = await eng.introspect_schema()
        assert isinstance(schema, dict)
        assert 'tables' in schema
    asyncio.run(_run())


