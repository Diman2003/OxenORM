Run with PostgreSQL in Docker:

1) Start Postgres

   docker compose up -d postgres

2) Set env for the app/tests:

   export OXEN_BLOG_DB=postgresql://oxenorm:oxenorm@localhost:5432/oxenorm

3) Run tests:

   PYTHONPATH=$(pwd) ./venv/bin/pytest -q

4) Run server:

   PYTHONPATH=$(pwd) ./venv/bin/uvicorn examples.blog_app.app:app --reload

Seed data:

   PYTHONPATH=$(pwd) OXEN_BLOG_DB=postgresql://oxenorm:oxenorm@localhost:5432/oxenorm ./venv/bin/python examples/blog_app/seed.py

Sample requests (after seeding):

- List users:

   curl -s http://localhost:8000/users | jq

- Create a post:

   curl -s -X POST http://localhost:8000/posts -H 'Content-Type: application/json' \
     -d '{"title":"New","body":"Body","author_id":1}' | jq

- Posts with authors (ORM select_related join):

   curl -s http://localhost:8000/posts/with-authors | jq

- Search posts (ORM Q with OR + icontains):

   curl -s 'http://localhost:8000/posts/search?query=oxen' | jq

- Top authors (ORM window function + Python aggregation):

   curl -s http://localhost:8000/analytics/top-authors | jq


