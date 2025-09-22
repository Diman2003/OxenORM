import asyncio, os, time
from oxen.rust_bridge import OxenEngine

MYSQL_URL = os.environ.get("OXEN_MYSQL_URL", "mysql://oxenorm:oxenorm@localhost:3306/oxenorm")

async def run():
    eng = OxenEngine(MYSQL_URL)
    time.sleep(5)
    await eng.connect()
    # Reset schema
    await eng.execute_query("DROP TABLE IF EXISTS orders")
    await eng.execute_query("DROP TABLE IF EXISTS users")
    await eng.execute_query("CREATE TABLE users (id BIGINT PRIMARY KEY AUTO_INCREMENT, username VARCHAR(100) UNIQUE, age INT, salary DOUBLE, tags JSON)")
    await eng.execute_query("CREATE TABLE orders (id BIGINT PRIMARY KEY AUTO_INCREMENT, user_id BIGINT, total DOUBLE)")

    # Insert users via IR
    users = [
        {"username": "u1", "age": 21, "salary": 55000.0, "tags": ["x", "y"]},
        {"username": "u2", "age": 29, "salary": 60000.0, "tags": ["a", "b"]},
        {"username": "alice_a", "age": 35, "salary": 70000.0, "tags": ["alpha"]},
        {"username": "alice_b", "age": 28, "salary": 68000.0, "tags": ["beta"]},
        {"username": "bob", "age": 25, "salary": 50000.0, "tags": ["gamma"]},
    ]
    for u in users:
        ir_ins = {"dialect": "mysql", "table": "users", "action": "insert", "set": u}
        await eng.execute_ir(ir_ins)

    # Lookup IDs
    async def get_id(username):
        ir_sel = {"dialect": "mysql", "table": "users", "select": ["id"], "filters": [{"field": "username", "op": "eq", "value": username}]}
        res = await eng.execute_ir(ir_sel)
        return res.get("data", [{}])[0].get("id")

    id_u1 = await get_id("u1")
    id_u2 = await get_id("u2")

    # Insert orders
    for total in (10.0, 20.0, 30.0):
        await eng.execute_ir({"dialect": "mysql", "table": "orders", "action": "insert", "set": {"user_id": id_u1, "total": total}})
        await eng.execute_ir({"dialect": "mysql", "table": "orders", "action": "insert", "set": {"user_id": id_u2, "total": total}})

    # 1) Basic filter + startswith + order/limit/offset
    ir1 = {"dialect": "mysql", "table": "users", "select": ["id", "username"],
           "filters": [{"field": "age", "op": "gte", "value": 20}, {"field": "username", "op": "startswith", "value": "u"}],
           "order_by": [{"field": "username", "direction": "desc"}], "limit": 2, "offset": 0}
    r1 = await eng.execute_ir(ir1)
    print("basic filter/order/limit:", r1)

    # 2) IN and NOT IN
    ir2 = {"dialect": "mysql", "table": "users", "select": ["username", "age"],
           "filters": [{"field": "age", "op": "in", "value": [25, 29, 35]}]}
    r2 = await eng.execute_ir(ir2)
    print("IN ages 25,29,35:", r2)

    ir2b = {"dialect": "mysql", "table": "users", "select": ["username", "age"],
           "filters": [{"field": "age", "op": "not_in", "value": [25, 29]}]}
    r2b = await eng.execute_ir(ir2b)
    print("NOT IN ages 25,29:", r2b)

    # 3) icontains on username
    ir3 = {"dialect": "mysql", "table": "users", "select": ["username"],
           "filters": [{"field": "username", "op": "icontains", "value": "ALIC"}]}
    r3 = await eng.execute_ir(ir3)
    print("icontains ALIC usernames:", r3)

    # 4) JOIN users->orders where total >= 20
    ir4 = {"dialect": "mysql", "table": "users", "select": ["users.username", "orders.total"],
           "joins": [{"join_type": "inner", "table": "orders", "on": {"left": "users.id", "op": "=", "right": "orders.user_id"}}],
           "filters": [{"field": "orders.total", "op": "gte", "value": 20}]}
    r4 = await eng.execute_ir(ir4)
    print("join users-orders total>=20 count:", len(r4.get("data", [])))

    # 5) UPDATE users starting with u -> age=99
    ir5 = {"dialect": "mysql", "table": "users", "action": "update", "set": {"age": 99},
           "filters": [{"field": "username", "op": "startswith", "value": "u"}]}
    r5 = await eng.execute_ir(ir5)
    print("update rows_affected:", r5.get("rows_affected"))

    # Verify update
    ir5b = {"dialect": "mysql", "table": "users", "select": ["count(*)"],
            "filters": [{"field": "age", "op": "eq", "value": 99}]}
    r5b = await eng.execute_ir(ir5b)
    print("verify age=99 count:", r5b.get("data"))

    # 6) DELETE age=99
    ir6 = {"dialect": "mysql", "table": "users", "action": "delete",
           "filters": [{"field": "age", "op": "eq", "value": 99}]}
    r6 = await eng.execute_ir(ir6)
    print("delete rows_affected:", r6.get("rows_affected"))

    # Remaining users count
    ir7 = {"dialect": "mysql", "table": "users", "select": ["count(*)"]}
    r7 = await eng.execute_ir(ir7)
    print("remaining users count:", r7.get("data"))

asyncio.run(run())
