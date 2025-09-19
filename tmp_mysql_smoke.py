import asyncio, os, time
from oxen.rust_bridge import OxenEngine

MYSQL_URL = os.environ.get("OXEN_MYSQL_URL", "mysql://oxenorm:oxenorm@localhost:3306/oxenorm")

async def try_mysql():
    eng = OxenEngine(MYSQL_URL)
    time.sleep(10)
    try:
        await eng.connect()
    except Exception as e:
        print("MySQL not reachable:", e)
        return
    try:
        await eng.execute_query("DROP TABLE IF EXISTS smoke_users")
    except Exception as e:
        print("Drop error (ignored):", e)
    await eng.execute_query("CREATE TABLE smoke_users (id BIGINT PRIMARY KEY AUTO_INCREMENT, username VARCHAR(100) UNIQUE, age INT, tags JSON)")

    rows = [{"username": f"user_{i}", "age": i % 50, "tags": ["a", "b"]} for i in range(0, 600)]
    ir_ins_many = {"dialect": "mysql", "table": "smoke_users", "action": "insert", "rows": rows}
    res_many = await eng.execute_ir(ir_ins_many)
    print("insert_many rows_affected:", res_many.get("rows_affected"))

    ir_sel = {"dialect": "mysql", "table": "smoke_users", "select": ["count(*)"]}
    res_sel = await eng.execute_ir(ir_sel)
    print("select count data:", res_sel.get("data"))

    ir_upd = {"dialect": "mysql", "table": "smoke_users", "action": "update", "set": {"age": 99}, "filters": [{"field": "username", "op": "startswith", "value": "user_"}]}
    res_upd = await eng.execute_ir(ir_upd)
    print("update rows_affected:", res_upd.get("rows_affected"))

    ir_del = {"dialect": "mysql", "table": "smoke_users", "action": "delete", "filters": [{"field": "age", "op": "eq", "value": 99}]}
    res_del = await eng.execute_ir(ir_del)
    print("delete rows_affected:", res_del.get("rows_affected"))

asyncio.run(try_mysql())
