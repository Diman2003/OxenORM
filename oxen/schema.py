from __future__ import annotations

from typing import Any, Type
import asyncio


def detect_dialect(connection_string: str) -> str:
    s = (connection_string or "").lower()
    if "postgres" in s:
        return "postgres"
    if "mysql" in s:
        return "mysql"
    return "sqlite"


def map_sql_type_for_dialect(base_type: str, dialect: str) -> str:
    if dialect == "postgres":
        if base_type == "REAL":
            return "DOUBLE PRECISION"
        if base_type == "DATETIME":
            return "TIMESTAMP"
        return base_type
    if dialect == "mysql":
        if base_type == "TIMESTAMP":
            return "DATETIME"
        return base_type
    return base_type


def generate_create_table_sql(model: Type[Any], dialect: str) -> str:
    """Generate CREATE TABLE IF NOT EXISTS DDL for a model, naïve create-only."""
    meta = model._meta
    cols: list[str] = []
    # Primary key
    if dialect == "postgres":
        cols.append("id SERIAL PRIMARY KEY")
    elif dialect == "mysql":
        cols.append("id BIGINT PRIMARY KEY AUTO_INCREMENT")
    else:
        cols.append("id INTEGER PRIMARY KEY AUTOINCREMENT")

    for name, field in meta.fields_map.items():
        if name == "id":
            continue
        # Derive base type from field
        base_type = getattr(field, "_get_sql_type", lambda: "TEXT")()
        sql_type = map_sql_type_for_dialect(base_type, dialect)
        not_null = "" if getattr(field, "null", True) else " NOT NULL"
        # For relational fields, just store FK as integer/bigint
        if field.__class__.__name__ in ("ForeignKeyField", "OneToOneField"):
            sql_type = "BIGINT" if dialect in ("postgres", "mysql") else "INTEGER"
        # Unique constraint
        unique = " UNIQUE" if getattr(field, "unique", False) else ""
        # Default value (simple constants only)
        default_clause = ""
        default = getattr(field, 'default', None)
        if default is not None and not callable(default):
            if isinstance(default, str):
                escaped = default.replace("\"", "\"\"")
                default_clause = f" DEFAULT \"{escaped}\""
            else:
                default_clause = f" DEFAULT {default}"
        # Auto timestamp defaults
        if base_type == "DATETIME" and getattr(field, 'auto_now_add', False):
            if dialect == 'postgres':
                default_clause = " DEFAULT CURRENT_TIMESTAMP"
            else:
                default_clause = " DEFAULT CURRENT_TIMESTAMP"
        cols.append(f"{name} {sql_type}{not_null}{unique}{default_clause}")

    table = meta.table_name
    return f"CREATE TABLE IF NOT EXISTS {table} (\n    " + ",\n    ".join(cols) + "\n)"


def ensure_table_exists_for_model(engine: Any, model: Type[Any]) -> None:
    """Synchronously ensure the model table exists by issuing CREATE TABLE IF NOT EXISTS."""
    # Detect dialect
    conn = getattr(engine, "_connection_string", getattr(engine, "connection_string", ""))
    dialect = detect_dialect(conn)
    ddl = generate_create_table_sql(model, dialect)
    # Call async execute_query from sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        if loop.is_running():
            # Fire-and-forget task in running loop
            loop.create_task(engine.execute_query(ddl))
        else:
            loop.run_until_complete(engine.execute_query(ddl))
    except Exception:
        # Best-effort: don't crash on schema sync
        pass


def _run_sync(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        # Fire-and-forget
        loop.create_task(coro)
        return None
    return loop.run_until_complete(coro)


async def _fetch_existing_columns(engine: Any, table: str, dialect: str) -> set[str]:
    cols: set[str] = set()
    if dialect == "postgres":
        sql = "SELECT column_name FROM information_schema.columns WHERE table_name = ?"
        res = await engine.execute_query(sql, [table])
        for row in (res.get('data') or []):
            name = row.get('column_name') or row.get('COLUMN_NAME') or row.get('column')
            if name:
                cols.add(str(name).lower())
    elif dialect == "mysql":
        sql = "SELECT column_name FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = ?"
        res = await engine.execute_query(sql, [table])
        for row in (res.get('data') or []):
            name = row.get('column_name') or row.get('COLUMN_NAME') or row.get('column')
            if name:
                cols.add(str(name).lower())
    else:
        # SQLite
        # Note: pragma doesn't support parameters reliably; inline safe table name
        res = await engine.execute_query(f'PRAGMA table_info("{table}")')
        for row in (res.get('data') or []):
            name = row.get('name') or row.get('NAME')
            if name:
                cols.add(str(name).lower())
    return cols


def sync_model(engine: Any, model: Type[Any]) -> None:
    """Ensure table exists and add missing columns (create-only, additive)."""
    # Create if not exists
    ensure_table_exists_for_model(engine, model)
    # Determine dialect
    conn = getattr(engine, "_connection_string", getattr(engine, "connection_string", ""))
    dialect = detect_dialect(conn)

    async def _sync():
        existing = await _fetch_existing_columns(engine, model._meta.table_name, dialect)
        additions: list[str] = []
        for name, field in model._meta.fields_map.items():
            col = name.lower()
            if col == 'id':
                continue
            if col in existing:
                continue
            base_type = getattr(field, "_get_sql_type", lambda: "TEXT")()
            sql_type = map_sql_type_for_dialect(base_type, dialect)
            if field.__class__.__name__ in ("ForeignKeyField", "OneToOneField"):
                sql_type = "BIGINT" if dialect in ("postgres", "mysql") else "INTEGER"
            not_null = "" if getattr(field, "null", True) else " NOT NULL"
            unique = " UNIQUE" if getattr(field, "unique", False) else ""
            default_clause = ""
            default = getattr(field, 'default', None)
            if default is not None and not callable(default):
                if isinstance(default, str):
                    escaped = default.replace("\"", "\"\"")
                    default_clause = f" DEFAULT \"{escaped}\""
                else:
                    default_clause = f" DEFAULT {default}"
            additions.append(f"ALTER TABLE {model._meta.table_name} ADD COLUMN {col} {sql_type}{not_null}{unique}{default_clause}")
        for stmt in additions:
            await engine.execute_query(stmt)

    _run_sync(_sync())


