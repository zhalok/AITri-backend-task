#!/usr/bin/env bash
# The one command for every test: server (rules, access control, visibility, concurrency, repositories), then the
# browser test (two browsers in one meeting).
#
#   ./scripts/test.sh                 # everything
#   ./scripts/test.sh server          # server tests only (needs just Postgres)
#   ./scripts/test.sh e2e             # the Playwright test only (needs the whole stack)
#   ./scripts/test.sh server -k audit # extra arguments go to pytest
#   HEADED=1 ./scripts/test.sh e2e    # watch the two browsers (headless by default, so it runs unattended)
#
# Postgres is started for you (docker compose). The server tests create and drop their own databases
# (l10_test, l10_concurrency), so the dev database is never touched. The e2e test drives the real stack
# (nginx -> API -> Postgres -> Redis), which compose starts here with the clock pinned by APP_NOW.
# Failure traces and the HTML report land in client/test-results and client/playwright-report.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WHICH="${1:-all}"
[ $# -gt 0 ] && shift || true
case "$WHICH" in all|server|e2e) ;; *) echo "usage: $0 [all|server|e2e] [pytest args]" >&2; exit 2;; esac

run_server() {
  docker compose up -d --wait db
  cd "$ROOT/server"
  if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
    .venv/bin/pip install --quiet -r requirements.txt
  fi
  .venv/bin/python -m pytest "$@"
}

run_e2e() {
  docker compose up -d --build --wait
  cd "$ROOT/client"
  [ -d node_modules ] || npm ci
  npx playwright install chromium >/dev/null
  npx playwright test
}

case "$WHICH" in
  server) (run_server "$@") ;;
  e2e)    (run_e2e) ;;
  all)    (run_server "$@"); (run_e2e) ;;
esac
