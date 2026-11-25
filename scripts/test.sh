#!/usr/bin/env bash
# The one command for every test. It starts the infrastructure, then runs the layer scripts in order:
#   1. infrastructure   docker compose up -d --build --wait   (Postgres, Redis, API, web; clock pinned by APP_NOW)
#   2. test-unit.sh     rules, services, controllers          (no infrastructure needed)
#   3. test-api.sh      access control, visibility, concurrency, repositories
#   4. test-e2e.sh      two browsers in one meeting (Playwright)
# Stops at the first failing layer. The stack is left running afterwards; stop it with: docker compose down
#
#   ./scripts/test.sh
#   HEADED=1 ./scripts/test.sh     # watch the browser test
# Run one layer alone with its own script, e.g. ./scripts/test-api.sh -k audit (the infrastructure must be up).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

docker compose up -d --build --wait

./scripts/test-unit.sh
./scripts/test-api.sh
./scripts/test-e2e.sh
