import asyncio, os, time
from oxen.rust_bridge import OxenEngine

PG_URL = os.environ.get("OXEN_DEMO_PG", "postgresql://oxenorm:oxenorm@localhost:5433/oxenorm")
MY_URL = os.environ.get("OXEN_DEMO_MY", "mysql://oxenorm:oxenorm@localhost:3307/oxenorm")

async def setup_postgres(eng: OxenEngine):
    await eng.execute_query('DROP TABLE IF EXISTS "orders"')
    await eng.execute_query('DROP TABLE IF EXISTS "users"')
    await eng.execute_query('CREATE TABLE "users" (id SERIAL PRIMARY KEY, username VARCHAR(100) UNIQUE, age INT, salary DOUBLE PRECISION, tags TEXT[])')
    await eng.execute_query('CREATE TABLE "orders" (id SERIAL PRIMARY KEY, user_id INT, total DOUBLE PRECISION)')

async def setup_mysql(eng: OxenEngine):
    await eng.execute_query('DROP TABLE IF EXISTS orders')
    await eng.execute_query('DROP TABLE IF EXISTS users')
    await eng.execute_query('CREATE TABLE users (id BIGINT PRIMARY KEY AUTO_INCREMENT, username VARCHAR(100) UNIQUE, age INT, salary DOUBLE, tags JSON)')
    await eng.execute_query('CREATE TABLE orders (id BIGINT PRIMARY KEY AUTO_INCREMENT, user_id BIGINT, total DOUBLE)')

async def seed_common(eng: OxenEngine, dialect: str):
    users = [
        {"username": "demo_u1", "age": 21, "salary": 55000.0, "tags": ["x", "y"]},
        {"username": "demo_u2", "age": 29, "salary": 60000.0, "tags": ["a", "b"]},
        {"username": "demo_alice", "age": 35, "salary": 70000.0, "tags": ["alpha"]},
        {"username": "demo_bob", "age": 25, "salary": 50000.0, "tags": ["gamma"]},
    ]
    for u in users:
        await eng.execute_ir({"dialect": dialect, "table": "users", "action": "insert", "set": u})

    # find ids
    async def get_id(name: str):
        res = await eng.execute_ir({"dialect": dialect, "table": "users", "select": ["id"], "filters": [{"field": "username", "op": "eq", "value": name}]})
        return res.get('data', [{}])[0].get('id')
    id1 = await get_id("demo_u1")
    id2 = await get_id("demo_u2")

    for tot in (10.0, 20.0, 30.0):
        await eng.execute_ir({"dialect": dialect, "table": "orders", "action": "insert", "set": {"user_id": id1, "total": tot}})
        await eng.execute_ir({"dialect": dialect, "table": "orders", "action": "insert", "set": {"user_id": id2, "total": tot}})

async def run_tests(eng: OxenEngine, dialect: str):
    # basic
    r1 = await eng.execute_ir({"dialect": dialect, "table": "users", "select": ["id", "username"], "filters": [{"field": "age", "op": "gte", "value": 20}], "order_by": [{"field": "username", "direction": "asc"}], "limit": 10})
    print(dialect, 'users>=20:', r1.get('rows_affected'))
    # icontains
    r2 = await eng.execute_ir({"dialect": dialect, "table": "users", "select": ["username"], "filters": [{"field": "username", "op": "icontains", "value": "DEMO_"}]})
    print(dialect, 'icontains DEMO_ usernames:', r2.get('rows_affected'))
    # join
    join = {"join_type": "inner", "table": "orders", "on": {"left": "users.id", "op": "=", "right": "orders.user_id"}}
    r3 = await eng.execute_ir({"dialect": dialect, "table": "users", "select": ["users.username", "orders.total"], "joins": [join], "filters": [{"field": "orders.total", "op": "gte", "value": 20}]})
    print(dialect, 'join count:', r3.get('rows_affected'))
    # update/delete
    r4 = await eng.execute_ir({"dialect": dialect, "table": "users", "action": "update", "set": {"age": 99}, "filters": [{"field": "username", "op": "startswith", "value": "demo_u"}]})
    print(dialect, 'update rows:', r4.get('rows_affected'))
    r5 = await eng.execute_ir({"dialect": dialect, "table": "users", "action": "delete", "filters": [{"field": "age", "op": "eq", "value": 99}]})
    print(dialect, 'delete rows:', r5.get('rows_affected'))

async def main():
    # Postgres
    pg = OxenEngine(PG_URL)
    try:
        await pg.connect()
        await setup_postgres(pg)
        await seed_common(pg, 'postgres')
        await run_tests(pg, 'postgres')
    except Exception as e:
        print('postgres error:', e)

    # MySQL
    my = OxenEngine(MY_URL)
    time.sleep(5)
    try:
        await my.connect()
        await setup_mysql(my)
        await seed_common(my, 'mysql')
        await run_tests(my, 'mysql')
    except Exception as e:
        print('mysql error:', e)

if __name__ == '__main__':
    asyncio.run(main())

