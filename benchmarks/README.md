Benchmark suite (Oxen vs SQLAlchemy vs Tortoise)

Setup

1) Ensure Postgres is running:

   docker compose up -d postgres

2) Install deps (in your venv):

   ./venv/bin/pip install -r requirements.txt

3) Optionally seed app data:

   PYTHONPATH=$(pwd) OXEN_BLOG_DB=postgresql://oxenorm:oxenorm@localhost:5432/oxenorm ./venv/bin/python examples/blog_app/seed.py

Run

   PYTHONPATH=$(pwd) OXEN_BENCH_DB=postgresql://oxenorm:oxenorm@localhost:5432/oxenorm \
   OXEN_BENCH_ITER=500 ./venv/bin/python benchmarks/perf_bench.py

Output

JSON with results per ORM and operation, e.g.:

{
  "oxen": [
    {"name": "oxen_read_one", "iterations": 500, "elapsed_s": 0.12, "qps": 4166.7},
    {"name": "oxen_read_many", "iterations": 500, "elapsed_s": 0.31, "qps": 1612.9}
  ],
  "sqlalchemy": [
    {"name": "sqlalchemy_read_one", ...},
    {"name": "sqlalchemy_read_many", ...}
  ],
  "tortoise": [
    {"name": "tortoise_read_one", ...},
    {"name": "tortoise_read_many", ...}
  ]
}

Notes

- You can change OXEN_BENCH_ITER to adjust iterations.
- For Django, you can add a similar bench module if desired; Django setup requires settings and manage.py which are not included here to keep footprint small.

