import asyncio, os
from oxen.rust_bridge import OxenEngine

PG_URL = os.environ.get("OXEN_PG_URL", "postgresql://oxenorm:oxenorm@localhost:5432/oxenorm")

async def try_pg():
    eng = OxenEngine(PG_URL)
    try:
        await eng.connect()
    except Exception as e:
        print("Postgres not reachable:", e)
        return
    try:
        await eng.execute_query("DROP TABLE IF EXISTS ""smoke_users""")
    except Exception as e:
        print("Drop error (ignored):", e)
    await eng.execute_query("CREATE TABLE ""smoke_users"" (id SERIAL PRIMARY KEY, username VARCHAR(100) UNIQUE, age INT, tags TEXT[])")

    rows = [{"username": f"user_{i}", "age": i % 50, "tags": ["a", "b"]} for i in range(0, 1200)]
    ir_ins_many = {"dialect": "postgres", "table": "smoke_users", "action": "insert", "rows": rows}
    res_many = await eng.execute_ir(ir_ins_many)
    print("insert_many rows_affected:", res_many.get("rows_affected"))

    ir_sel = {"dialect": "postgres", "table": "smoke_users", "select": ["count(*)"],}
    res_sel = await eng.execute_ir(ir_sel)
    print("select count data:", res_sel.get("data"))

    ir_upd = {"dialect": "postgres", "table": "smoke_users", "action": "update", "set": {"age": 99}, "filters": [{"field": "username", "op": "startswith", "value": "user_"}], "returning": ["id"]}
    res_upd = await eng.execute_ir(ir_upd)
    print("update returning rows:", len(res_upd.get("data", [])))

    ir_del = {"dialect": "postgres", "table": "smoke_users", "action": "delete", "filters": [{"field": "age", "op": "eq", "value": 99}]}
    res_del = await eng.execute_ir(ir_del)
    print("delete rows_affected:", res_del.get("rows_affected"))

asyncio.run(try_pg())
