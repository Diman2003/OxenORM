import asyncio, json
from oxen_engine import build_sql_json
from oxen.rust_bridge import OxenEngine

print('=== Build-only smoke ===')
irs = [
    {
        "dialect": "sqlite",
        "table": "users",
        "select": ["id", "username"],
        "filters": [{"field": "age", "op": "gte", "value": 30}],
        "order_by": [{"field": "username", "direction": "asc"}],
        "limit": 10,
        "offset": 5,
    },
    {
        "dialect": "sqlite",
        "table": "users",
        "action": "insert",
        "set": {"username": "alice", "age": 30, "salary": 50000.5}
    },
    {
        "dialect": "sqlite",
        "table": "users",
        "action": "update",
        "set": {"salary": 51000.0},
        "filters": [{"field": "username", "op": "eq", "value": "alice"}]
    },
]
for ir in irs:
    built = build_sql_json(json.dumps(ir))
    print(built)

print('\n=== SQLite execute smoke ===')

async def run_sqlite_smoke():
    eng = OxenEngine("sqlite://smoke_test.db")
    await eng.connect()
    # Clean slate
    await eng.drop_table("users")
    await eng.create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "username": "TEXT UNIQUE",
        "age": "INTEGER",
        "salary": "REAL"
    })
    # Insert via IR
    ir_ins = {
        "dialect": "sqlite",
        "table": "users",
        "action": "insert",
        "set": {"username": "alice", "age": 30, "salary": 50000.5}
    }
    res_ins = await eng.execute_ir(ir_ins)
    print('insert:', res_ins)

    # Select via IR
    ir_sel = {
        "dialect": "sqlite",
        "table": "users",
        "select": ["id", "username", "age", "salary"],
        "filters": [{"field": "username", "op": "eq", "value": "alice"}],
    }
    res_sel = await eng.execute_ir(ir_sel)
    print('select:', res_sel)

    # Update via IR
    ir_upd = {
        "dialect": "sqlite",
        "table": "users",
        "action": "update",
        "set": {"salary": 51000.0},
        "filters": [{"field": "username", "op": "eq", "value": "alice"}],
    }
    res_upd = await eng.execute_ir(ir_upd)
    print('update:', res_upd)

    # Delete via IR
    ir_del = {
        "dialect": "sqlite",
        "table": "users",
        "action": "delete",
        "filters": [{"field": "username", "op": "eq", "value": "alice"}],
    }
    res_del = await eng.execute_ir(ir_del)
    print('delete:', res_del)

asyncio.run(run_sqlite_smoke())
