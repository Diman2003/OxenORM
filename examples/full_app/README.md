Full App Demo (OxenORM)

What this shows
- Models: Account, CustomerProfile (OneToOne), Address (FK), Product, Order, OrderItem
- Auto schema: Tables are created automatically when binding models to a database engine
- Features: CRUD, filters (eq/ne/lt/lte/gt/gte/in/not_in/contains/icontains/startswith/istartswith/endswith/iendswith/isnull/notnull), joins, grouping/aggregation, CTE passthrough, and basic window-like outputs
- Dialects: Postgres (5440) and MySQL (3310) via docker-compose

Quickstart
1) Start databases:
   docker compose up -d
2) Activate your Python venv where OxenORM is installed (maturin develop).
3) Run demo:
   PYTHONPATH=$PWD python examples/full_app/business_logic.py

Notes
- No manual migration files needed; models auto-create tables when you bind the engine (Model._set_rust_engine).
- To run both services and the demo with one command, use:
   PYTHONPATH=$PWD python examples/full_app/run_all.py

Expected output highlights
- Creates accounts, addresses, profiles, products, orders.
- Prints user lists (filters/order), counts, aggregates.
- Validates joins and CRUD operations across Postgres and MySQL.

