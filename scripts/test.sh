#!/usr/bin/env bash
# One command for the server tests: rules (unit), access control, data visibility, concurrency, repositories.
#
#   ./scripts/test.sh                  # everything under server/tests (unit + service + repository + API)
#   ./scripts/test.sh tests/unit       # one layer; extra arguments go straight to pytest
#
# It starts Postgres itself (docker compose, db service only) and waits until it is healthy. The tests create and
# drop their own databases (l10_test, l10_concurrency) on that server, so the dev database is never touched.
# Time is fixed by APP_NOW (see server/tests/conftest.py); nothing here depends on the wall clock.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

docker compose up -d --wait db

cd server
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install --quiet -r requirements.txt
fi

exec .venv/bin/python -m pytest "$@"
