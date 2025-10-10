#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/bench.sh [iter]
ITER="${1:-500}"

# Ensure venv is active
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "Please activate venv first (source venv/bin/activate)" >&2
  exit 1
fi

mkdir -p benchmarks

# SQLite run
export OXEN_BENCH_ITER="$ITER"
python benchmarks/perf_bench.py | tee benchmarks/last_results_sqlite.json >/dev/null
cat benchmarks/last_results_sqlite.json | python tools/format_bench.py >/dev/null

# Postgres run (requires Docker)
if command -v docker >/dev/null 2>&1; then
  docker compose up -d postgres
  # wait for health
  for i in {1..60}; do
    status=$(docker inspect --format='{{.State.Health.Status}}' oxen_postgres 2>/dev/null || echo starting)
    [[ "$status" == "healthy" ]] && break
    sleep 2
  done
  export OXEN_BENCH_DB="postgresql://oxenorm:oxenorm@localhost:5432/oxenorm"
  export OXEN_BENCH_ITER="$ITER"
  export OXEN_MIN_OVERHEAD=1
  export OXEN_PG_COPY=1
  python benchmarks/perf_bench.py | tee benchmarks/last_results_pg.json >/dev/null
  cat benchmarks/last_results_pg.json | python tools/format_bench.py >/dev/null
fi

echo "Artifacts written to benchmarks/: normalized_results.json, core_qps.csv, extended_qps.csv (last run)"
