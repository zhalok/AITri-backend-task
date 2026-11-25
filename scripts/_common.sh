# Shared by the test scripts (sourced, not run).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The server's Python environment, created on first use.
ensure_venv() {
  cd "$ROOT/server"
  if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
    .venv/bin/pip install --quiet -r requirements.txt
  fi
}

# Fails fast, with the fix, when Postgres is not up.
require_postgres() {
  if ! docker compose -f "$ROOT/docker-compose.yml" exec -T db pg_isready -U postgres >/dev/null 2>&1; then
    echo "Postgres is not running. Start the infrastructure with ./scripts/test.sh, or: docker compose up -d --wait db" >&2
    exit 1
  fi
}
