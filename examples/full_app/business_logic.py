import asyncio, os
from datetime import datetime
from oxen.rust_bridge import OxenEngine
from models import Account, CustomerProfile, Address, Product, Order, OrderItem

PG_URL = os.environ.get("OXEN_FULL_PG", "postgresql://oxenorm:oxenorm@localhost:5440/oxenorm")
MY_URL = os.environ.get("OXEN_FULL_MY", "mysql://oxenorm:oxenorm@localhost:3310/oxenorm")

async def seed_common(db):
    # Bind models
    for m in (Account, CustomerProfile, Address, Product, Order, OrderItem):
        m._set_rust_engine(db)
    # Create accounts
    await Account.create(username='alice', email='alice@example.com')  # type: ignore
    await Account.create(username='bob', email='bob@example.com')  # type: ignore
    # Re-fetch to ensure PKs populated across dialects
    a1 = await Account.get(username='alice')
    a2 = await Account.get(username='bob')
    # Address
    await Address.create(add_user=a1.pk, add_line1='1 Main', add_line2='Apt 2', city='NY', state='NY', country='US', zipcode=10001, is_default=True)  # type: ignore
    await CustomerProfile.create(profile_type='Personal', kt_id='KT', auth_id=a1, profile_pic='p1.jpg', qr_code='q1.jpg')  # type: ignore
    # Products
    p1 = await Product.create(name='Widget', price=10.0)  # type: ignore
    p2 = await Product.create(name='Gadget', price=20.0)  # type: ignore
    # Order
    await Order.create(account=a1.pk, created_at=datetime.now())  # type: ignore
    # Re-fetch latest order id
    latest = await Order.filter(account=a1.pk).order_by('-id').limit(1)
    o1_id = latest[0].pk if latest else None
    await OrderItem.create(order_ref=o1_id, product=p1.pk, quantity=2, unit_price=10.0)  # type: ignore
    await OrderItem.create(order_ref=o1_id, product=p2.pk, quantity=1, unit_price=20.0)  # type: ignore

async def run_crud(db):
    Account._set_rust_engine(db)
    # Filter icontains, order, limit
    users = await Account.filter(username__icontains='a').order_by('-username').limit(10)
    print('users:', [u.username for u in users])
    # Update
    if users:
        u = users[0]
        u.email = 'new_'+u.email
        await u.save()
    # Delete non-existing filter test: do nothing
    _ = await Account.filter(username='nobody').delete()

async def run_aggregates_cte_window(db):
    # Simple aggregate via values and count
    Product._set_rust_engine(db)
    cnt = await Product.count()
    print('product count:', cnt)
    # CTE example: top orders users (builder supports with_sql passthrough); use raw simple example
    from oxen_engine import build_sql_json
    import json
    dialect = 'postgres' if 'postgresql' in getattr(db, 'connection_string', '').lower() else 'mysql'
    ir = {
        'dialect': dialect,
        'table': 'orders',
        'select': ['user', 'COUNT(*) as cnt'],
        'groups': [],
        'filters': [],
        'order_by': [{'field': 'cnt', 'direction': 'desc'}],
        'with_sql': None,
    }
    built = build_sql_json(json.dumps(ir))
    res = await db.execute_query(built['sql'], built['params'])
    print('orders grouped:', res.get('data'))

async def main():
    pg = OxenEngine(PG_URL)
    await pg.connect()
    await seed_common(pg)
    await run_crud(pg)
    await run_aggregates_cte_window(pg)

    my = OxenEngine(MY_URL)
    await my.connect()
    await seed_common(my)
    await run_crud(my)
    await run_aggregates_cte_window(my)

if __name__ == '__main__':
    asyncio.run(main())

