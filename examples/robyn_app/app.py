import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from robyn import Robyn

from oxen.rust_bridge import OxenEngine
from examples.full_app.models import (
    Account,
    CustomerProfile,
    Address,
    Product,
    Order,
    OrderItem,
)


# --- Config ---
PORT = int(os.environ.get("OXEN_ROBYN_PORT", "8080"))
DB_URL = os.environ.get(
    "OXEN_ROBYN_DB_URL",
    os.environ.get("OXEN_FULL_PG", "postgresql://oxenorm:oxenorm@localhost:5440/oxenorm"),
)


app = Robyn(__file__)


# --- Engine binding & auto schema ---
_engine: Optional[OxenEngine] = None


async def get_engine() -> OxenEngine:
    global _engine
    if _engine is None:
        eng = OxenEngine(DB_URL)
        await eng.connect()
        # Bind models (auto create/add columns via model hook)
        Account._set_rust_engine(eng)
        CustomerProfile._set_rust_engine(eng)
        Address._set_rust_engine(eng)
        Product._set_rust_engine(eng)
        Order._set_rust_engine(eng)
        OrderItem._set_rust_engine(eng)
        _engine = eng
    return _engine


# --- Helpers ---
def json_response(data: Any, status: int = 200) -> Dict[str, Any]:
    return {
        "status_code": status,
        "body": json.dumps(data, default=str),
        "headers": {"Content-Type": "application/json"},
    }


def model_to_dict(obj: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {"id": getattr(obj, obj._meta.pk_attr)}
    for field in obj._meta.db_fields:
        if field == obj._meta.pk_attr:
            continue
        out[field] = getattr(obj, field, None)
    return out


def parse_json_body(request) -> Dict[str, Any]:
    try:
        raw = getattr(request, 'body', None)
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, (bytes, bytearray)):
            try:
                return json.loads(raw.decode('utf-8'))
            except Exception:
                return {}
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return {}
        # Fallback: Robyn might parse form data into request.json
        j = getattr(request, 'json', None)
        if isinstance(j, dict):
            return j
    except Exception:
        pass
    return {}


# --- Routes ---
@app.get("/health")
async def health(request):
    return json_response({"ok": True, "db_url": DB_URL})


# Accounts CRUD
@app.get("/accounts")
async def list_accounts(request):
    eng = await get_engine()
    users = await Account.filter().order_by("username").limit(100)
    out = []
    for u in users:
        d = model_to_dict(u)
        if d.get("id") in (None, 0, False):
            # Fallback: fetch id by unique username
            res = await eng.execute_query('SELECT "id" FROM "account" WHERE "username" = ? ORDER BY "id" DESC LIMIT 1', [u.username])
            row = (res.get('data') or [{}])[0]
            uid = row.get('id')
            if uid:
                d['id'] = uid
        out.append(d)
    return json_response(out)


@app.post("/accounts")
async def create_account(request):
    eng = await get_engine()
    payload = parse_json_body(request)
    username = payload.get("username")
    email = payload.get("email")
    if not username:
        return json_response({"error": "username required"}, 400)
    dsn = DB_URL.lower()
    if 'postgres' in dsn:
        ins = await eng.execute_query('INSERT INTO "account" ("username","email") VALUES (?,?) RETURNING "id","username","email"', [username, email])
        row = (ins.get('data') or [{}])[0]
        return json_response({"id": row.get('id'), "username": row.get('username'), "email": row.get('email')}, 201)
    else:
        # MySQL/SQLite fallback
        await eng.execute_query('INSERT INTO account (username,email) VALUES (?,?)', [username, email])
        if 'mysql' in dsn:
            rid = await eng.execute_query('SELECT LAST_INSERT_ID() as id')
            row = (rid.get('data') or [{}])[0]
            new_id = row.get('id')
        else:
            rid = await eng.execute_query('SELECT last_insert_rowid() as id')
            row = (rid.get('data') or [{}])[0]
            new_id = row.get('id')
        return json_response({"id": new_id, "username": username, "email": email}, 201)


@app.get("/accounts/:id")
async def get_account(request):
    await get_engine()
    acc_id = int(request.path_params["id"])
    items = await Account.filter(id=acc_id).limit(1)
    if not items:
        return json_response({"error": "not found"}, 404)
    return json_response(model_to_dict(items[0]))


@app.put("/accounts/:id")
async def update_account(request):
    await get_engine()
    acc_id = int(request.path_params["id"])
    payload = json.loads(request.body or "{}")
    items = await Account.filter(id=acc_id).limit(1)
    if not items:
        return json_response({"error": "not found"}, 404)
    obj = items[0]
    if "username" in payload:
        obj.username = payload["username"]
    if "email" in payload:
        obj.email = payload["email"]
    await obj.save()
    return json_response(model_to_dict(obj))


@app.delete("/accounts/:id")
async def delete_account(request):
    await get_engine()
    acc_id = int(request.path_params["id"]) 
    items = await Account.filter(id=acc_id).limit(1)
    if not items:
        return json_response({"error": "not found"}, 404)
    await items[0].delete()
    return json_response({"deleted": True})


# Products CRUD (list/create only for brevity)
@app.get("/products")
async def list_products(request):
    eng = await get_engine()
    items = await Product.filter().order_by("name").limit(100)
    out = []
    for p in items:
        d = model_to_dict(p)
        if d.get("id") in (None, 0, False):
            res = await eng.execute_query('SELECT "id" FROM "product" WHERE "name" = ? ORDER BY "id" DESC LIMIT 1', [p.name])
            row = (res.get('data') or [{}])[0]
            pid = row.get('id')
            if pid:
                d['id'] = pid
        out.append(d)
    return json_response(out)


@app.post("/products")
async def create_product(request):
    eng = await get_engine()
    payload = parse_json_body(request)
    name = payload.get("name")
    price = float(payload.get("price", 0.0))
    if not name:
        return json_response({"error": "name required"}, 400)
    dsn = DB_URL.lower()
    if 'postgres' in dsn:
        ins = await eng.execute_query('INSERT INTO "product" ("name","price") VALUES (?,?) RETURNING "id","name","price"', [name, price])
        row = (ins.get('data') or [{}])[0]
        return json_response({"id": row.get('id'), "name": row.get('name'), "price": row.get('price')}, 201)
    else:
        await eng.execute_query('INSERT INTO product (name,price) VALUES (?,?)', [name, price])
        if 'mysql' in dsn:
            rid = await eng.execute_query('SELECT LAST_INSERT_ID() as id')
        else:
            rid = await eng.execute_query('SELECT last_insert_rowid() as id')
        row = (rid.get('data') or [{}])[0]
        return json_response({"id": row.get('id'), "name": name, "price": price}, 201)


# Orders
@app.post("/orders")
async def create_order(request):
    eng = await get_engine()
    payload = parse_json_body(request)
    account_id = payload.get("account_id")
    items = payload.get("items", [])  # [{product_id, quantity}]
    if not account_id or not isinstance(items, list):
        return json_response({"error": "account_id and items[] required"}, 400)

    # Create order
    dsn = DB_URL.lower()
    if 'postgres' in dsn:
        ins = await eng.execute_query('INSERT INTO "orders" ("account","created_at") VALUES (?,?) RETURNING "id"', [account_id, datetime.now()])
        row = (ins.get('data') or [{}])[0]
        order_id = row.get('id')
    else:
        await eng.execute_query('INSERT INTO orders (account,created_at) VALUES (?,?)', [account_id, datetime.now().isoformat()])
        if 'mysql' in dsn:
            rid = await eng.execute_query('SELECT LAST_INSERT_ID() as id')
        else:
            rid = await eng.execute_query('SELECT last_insert_rowid() as id')
        row = (rid.get('data') or [{}])[0]
        order_id = row.get('id')
    if not order_id:
        return json_response({"error": "order create failed"}, 500)

    # Insert items
    created = []
    for it in items:
        pid = it.get("product_id")
        qty = int(it.get("quantity", 1))
        prod = await Product.filter(id=pid).limit(1)
        if not prod:
            return json_response({"error": f"product {pid} not found"}, 400)
        unit_price = float(prod[0].price)
        oi = await OrderItem.create(order_ref=order_id, product=pid, quantity=qty, unit_price=unit_price)  # type: ignore
        created.append(model_to_dict(oi))

    return json_response({"order_id": order_id, "items": created}, 201)


@app.get("/orders/:id")
async def get_order(request):
    await get_engine()
    oid = int(request.path_params["id"])
    orders = await Order.filter(id=oid).limit(1)
    if not orders:
        return json_response({"error": "not found"}, 404)
    order = orders[0]
    # Fetch items and products
    items = await OrderItem.filter(order_ref=order.pk)
    out_items: List[Dict[str, Any]] = []
    for it in items:
        prod = await Product.filter(id=it.product).limit(1)
        out = model_to_dict(it)
        out["product_detail"] = model_to_dict(prod[0]) if prod else None
        out_items.append(out)
    return json_response({
        "order": model_to_dict(order),
        "items": out_items,
    })


if __name__ == "__main__":
    app.start(port=PORT, host="0.0.0.0")


