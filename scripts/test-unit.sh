#!/usr/bin/env bash
# Unit tests: no database, no network. The business rules (every rule in 2.6, with boundary cases), the services
# and the controllers, with their collaborators faked.   Extra arguments go to pytest.
#
#   ./scripts/test-unit.sh
#   ./scripts/test-unit.sh -k rock
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
ensure_venv
exec .venv/bin/python -m pytest tests/unit tests/service tests/controller "$@"
