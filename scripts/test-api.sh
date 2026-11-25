#!/usr/bin/env bash
# API tests: real HTTP requests into the real app, against real Postgres (needs the db service to be up).
#   tests/api              access control (RBAC), with an in-memory store
#   tests/api_db           data visibility and team isolation, against the seeded database
#   tests/api_concurrency  simultaneous Make it an Issue requests leave one Issue
#   tests/repository       the SQL itself: queries, constraints, triggers, the audit trail
# The tests create and drop their own databases (l10_test, l10_concurrency); the dev database is never touched.
# The clock is pinned by APP_NOW (tests/conftest.py).   Extra arguments go to pytest.
#
#   ./scripts/test-api.sh
#   ./scripts/test-api.sh tests/api_concurrency -v
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
require_postgres
ensure_venv
if [ $# -eq 0 ]; then set -- tests/api tests/api_db tests/api_concurrency tests/repository; fi
exec .venv/bin/python -m pytest "$@"
