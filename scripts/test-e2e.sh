#!/usr/bin/env bash
# End-to-end test: two real browsers in one meeting; the facilitator advances the agenda and the second follows.
# Drives the whole stack through nginx (needs ./scripts/test.sh's infrastructure, i.e. docker compose up).
# Traces and the HTML report land in client/test-results and client/playwright-report.
#
#   ./scripts/test-e2e.sh
#   HEADED=1 ./scripts/test-e2e.sh                      # watch it: side-by-side windows, cursor, pauses
#   HEADED=1 STEP_DELAY_MS=4000 SCREEN_WIDTH=1728 ./scripts/test-e2e.sh
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
URL="${E2E_BASE_URL:-http://localhost:8080}"
if ! curl -fsS -o /dev/null "$URL/api/openapi.json"; then
  echo "The stack is not reachable at $URL. Start it with ./scripts/test.sh, or: docker compose up -d --build --wait" >&2
  exit 1
fi
cd "$ROOT/client"
[ -d node_modules ] || npm ci
npx playwright install chromium >/dev/null
exec npx playwright test "$@"
