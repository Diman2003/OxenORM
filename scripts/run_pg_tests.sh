#!/usr/bin/env bash
set -euo pipefail

# Start Postgres
if ! docker ps --format '{{.Names}}' | grep -q '^oxenorm-postgres$'; then
  docker compose up -d postgres
fi

# Wait for health
printf "Waiting for Postgres to be healthy"
for i in {1..60}; do
  status=$(docker inspect --format='{{.State.Health.Status}}' oxenorm-postgres || echo starting)
  if [ "$status" = "healthy" ]; then
    echo " - ready"
    break
  fi
  printf "."
  sleep 2
  if [ $i -eq 60 ]; then
    echo "\nPostgres did not become healthy in time" >&2
    exit 1
  fi
done

# Run tests
source venv/bin/activate
export OXEN_RUST_BACKEND=1
pytest -q tests/test_postgresql_simple.py tests/test_postgresql_advanced_features.py tests/test_postgresql_debug.py -q
