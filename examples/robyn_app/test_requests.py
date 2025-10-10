import json
import os
import time
import requests


BASE = os.environ.get("ROBYN_BASE", "http://localhost:8090")


def parse(resp):
    try:
        data = resp.json()
        body = data.get("body")
        if isinstance(body, str):
            try:
                return json.loads(body)
            except Exception:
                return body
        return data
    except Exception:
        return {"status": resp.status_code, "text": resp.text}


def main():
    out = {}
    # health
    r = requests.get(f"{BASE}/health", timeout=5)
    out["health"] = parse(r)

    # create account
    r = requests.post(
        f"{BASE}/accounts",
        json={"username": "robyn_user", "email": "robyn@example.com"},
        timeout=5,
    )
    acc = parse(r)
    out["create_account"] = acc
    acc_id = (acc or {}).get("id")

    # list accounts
    r = requests.get(f"{BASE}/accounts", timeout=5)
    out["list_accounts"] = parse(r)

    # create products
    r = requests.post(
        f"{BASE}/products",
        json={"name": "Widget", "price": 10.5},
        timeout=5,
    )
    p1 = parse(r)
    r = requests.post(
        f"{BASE}/products",
        json={"name": "Gadget", "price": 20.0},
        timeout=5,
    )
    p2 = parse(r)
    out["create_products"] = [p1, p2]

    # list products
    r = requests.get(f"{BASE}/products", timeout=5)
    products = parse(r)
    out["list_products"] = products

    # create order
    pid = None
    if isinstance(products, list) and products:
        pid = products[0].get("id")
    if acc_id and pid:
        r = requests.post(
            f"{BASE}/orders",
            json={"account_id": acc_id, "items": [{"product_id": pid, "quantity": 2}]},
            timeout=5,
        )
        order = parse(r)
        out["create_order"] = order
        order_id = (order or {}).get("order_id")
        if order_id:
            r = requests.get(f"{BASE}/orders/{order_id}", timeout=5)
            out["get_order"] = parse(r)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()


