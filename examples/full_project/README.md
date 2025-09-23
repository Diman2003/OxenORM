OxenORM Full Project Demo

This example brings up Postgres and MySQL with Docker, then seeds and tests OxenORM via the Rust IR builder.

Prerequisites
- Docker and docker compose
- Python 3.12 venv with OxenORM installed (maturin develop)

Run
1. Start databases:
   docker compose up -d
2. Activate your venv where OxenORM is installed.
3. Run the demo:
   python seed_and_test.py

It will:
- Create tables in Postgres and MySQL
- Seed demo data
- Run CRUD, joins, filters, updates, and deletes

