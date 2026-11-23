"""Test configuration.

Clock strategy: nothing reads the system clock for business time. Production code takes "now" from
APP_NOW; here it is pinned to the seed's "now" (2026-11-11T15:00:00Z, Wednesday 9:00 AM Chicago),
and service tests build a Clock at any instant they need. Auth tokens use the real clock on purpose.

Database strategy: tests never touch the dev database. DATABASE_URL is forced to a separate
`l10_test` database on the same Postgres (override with TEST_DATABASE_URL). Repository tests build
its schema from the real Alembic migrations, then run each test in a transaction that is rolled back.
"""
import os

# Must run before anything imports app.* (settings and the engine are created at import time).
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/l10_test"
)
os.environ["APP_NOW"] = "2026-11-11T15:00:00Z"
os.environ["COMPANY_TIMEZONE"] = "America/Chicago"
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-32b"
os.environ["JWT_EXPIRE_MINUTES"] = "480"

import pytest  # noqa: E402

from tests.helpers import make_clock  # noqa: E402


@pytest.fixture
def clock():
    """Fixed clock at the seed's 'now'."""
    return make_clock()
