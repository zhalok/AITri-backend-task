# Level 10 Meeting

A weekly team-meeting app: a Scorecard of Measurables, Rocks, Issues and To-Dos, and a live meeting that
several people attend at once. FastAPI + Postgres + Redis behind nginx, with a React front end.

## Start the infrastructure

You need Docker (with Compose). From the repository root:

```bash
docker compose up -d --build --wait
```

This builds and starts four containers and waits until each is healthy:

| Service | What it is | Reachable at |
|---|---|---|
| `db` | Postgres 16 (migrations and the seed run when the API starts) | `localhost:5432` |
| `redis` | Redis 7, the fan-out for live meeting updates | internal only |
| `api` | FastAPI app | internal only, through nginx |
| `web` | nginx: serves the React app and forwards `/api` to the API | http://localhost:8080 (https://localhost:8443, self-signed) |

Then open http://localhost:8080 and sign in with a seeded email, for example `avery@acme.test` (Admin),
`blake@acme.test` (Team Member) or `ellis@acme.test` (Observer). The API docs are at http://localhost:8080/api/docs.

The server clock is pinned to the seed's "now" (`APP_NOW`, 2026-11-11T15:00:00Z) in `docker-compose.yml`, so
the data and the statuses are the same on every run.

```bash
docker compose down        # stop
docker compose down -v     # stop and delete the database volume: the next start is a freshly seeded database
```

## Run the tests

One command runs everything. It starts the infrastructure above, then the three layers in order, and stops at
the first failure:

```bash
./scripts/test.sh
```

By default the browser test is **headless**, so the command runs unattended. To watch it instead, set `HEADED=1`:

```bash
HEADED=1 ./scripts/test.sh
```

Headed mode opens two real browser windows side by side (Blake on the left, Casey on the right), draws a red
cursor that glides to each button with a ripple on every click, and pauses after each step. Tune it with:

| Variable | Default | Meaning |
|---|---|---|
| `HEADED` | unset (headless) | `1` opens the browser windows |
| `STEP_DELAY_MS` | `2000` | pause after each step, headed only |
| `SCREEN_WIDTH`, `SCREEN_HEIGHT` | `1440`, `900` | your display size, used to split the screen in half |

For example: `HEADED=1 STEP_DELAY_MS=4000 SCREEN_WIDTH=1728 ./scripts/test.sh`.

### The three layers

Each layer has its own script. The unit script needs nothing. The API and end-to-end scripts assume the
infrastructure is already up (`./scripts/test.sh` starts it; or run `docker compose up -d --build --wait` yourself)
and print how to start it if it is not. Extra arguments go to the
test runner, so you can run a single layer or a single test.

**1. Unit tests: `./scripts/test-unit.sh`.** No database and no network. These check the business rules
directly, each with its boundary cases: Measurable status (`tests/unit/test_measurable_status.py`), Rock status and
progress, the To-Do completion rate and its rounding, the role-by-action access matrix, and the clock. The services
and controllers are tested next to them with their collaborators faked. Runs in seconds.
Example: `./scripts/test-unit.sh -k rock`.

**2. API tests: `./scripts/test-api.sh`.** Real HTTP requests into the real FastAPI app, with a real signed-in
user. Needs Postgres. Together they prove:
- *Access control:* a Team Member reading another team's data is refused, an Observer's write is refused (`tests/api`).
- *Data visibility and team isolation:* the queries that decide who sees what, run against the seeded database (`tests/api_db`).
- *Concurrency:* simultaneous Make it an Issue requests for the same Measurable and week return one Issue; the
  extra requests get the existing one back (`tests/api_concurrency`).
- *The SQL itself, on the seed:* queries, constraints, the append-only audit trail, and the meeting summaries for
  the two seeded meetings (`tests/repository`).

The tests create and drop their own databases (`l10_test`, `l10_concurrency`) on the same Postgres, so your dev
data is never touched. Example: `./scripts/test-api.sh tests/api_concurrency -v`.

**3. End-to-end test: `./scripts/test-e2e.sh`.** One Playwright test, two browsers, the whole stack through
nginx. Blake signs in and starts a meeting. Casey signs in afterwards, sees **Join meeting** (not Start), and
joins. Blake advances the agenda; Casey's page follows on its own, with no reload. It ends the meeting when it
finishes, so it can be run again on the same stack. Playwright saves a trace of every run in
`client/test-results/`, and the HTML report in `client/playwright-report/`; open a trace with
`npx playwright show-trace <path>/trace.zip`. A trace of a failing run (Redis stopped, so the second browser
cannot follow) is kept in `client/e2e/artifacts/failure-trace-no-redis.zip`.

## About the seed data

- "Now" for the seed is **2026-11-11T15:00:00Z** (Wednesday, November 11, 2026, 9:00 AM Chicago). Your app reads "now" from `APP_NOW` and defaults to this value.
- The company time zone is America/Chicago. All timestamps in the file are UTC.
- Weeks are named by their Monday in company time (`week_start`), for example `2026-11-02`.
- Dates without a time (`due_date`) are calendar dates in company time.
- `source` on an Issue links it to a Measurable and week. `source_issue_id` on a To-Do links it to an Issue.
- The two meetings in `meetings` have already ended. Their summaries are part of the rules report.
- Keep the ids from `seed.json` (`u1`, `m1`, `t12`, ...). The rules report is keyed by them.

## Rules report format

Your rules report command prints this JSON for the current `APP_NOW`, computed on a freshly seeded database (no data added while testing). We will also run it at other dates, so compute every value from the data.

- Include every team, and every Measurable with all 13 weeks ending with the current week (Aug 17 to Nov 9 at the default `APP_NOW`).
- Include every one of those weeks in `todo_completion`. A week with nothing due is `null`.
- "Today" (for overdue To-Dos and past-due Milestones) is the date of `APP_NOW` in company time.
- Status values are `on_track`, `off_track` or `pending`. Rock status is `on_track`, `off_track` or `complete`.
- Percentages are whole numbers, rounded half up. Ratings have one decimal, rounded half up.
- Lists of ids are sorted as plain strings (`t12` before `t30`), except `issue_order`, which lists unsolved Issues in Issue order.
- `meetings` covers ended meetings, keyed by meeting id. `scorecard_week` is the week the meeting reviewed. `rating` is `null` if no one rated.

```json
{
  "now": "<APP_NOW, ISO 8601 UTC>",
  "teams": {
    "<team_id>": {
      "measurable_status": {"<measurable_id>": {"<week_start>": "on_track | off_track | pending"}},
      "todo_completion": {"<week_start>": "null, or {due, done, rate_percent, meets_target}"},
      "overdue_todos": ["<todo_id>"],
      "rocks": {"<rock_id>": {"status": "on_track | off_track | complete", "progress_percent": 0}},
      "issue_order": ["<issue_id>"],
      "meetings": {
        "<meeting_id>": {
          "scorecard_week": "<week_start>",
          "measurable_status": {"<measurable_id>": "on_track | off_track | pending"},
          "issues_solved": ["<issue_id>"],
          "todos_created": ["<todo_id>"],
          "attendee_ids": ["<user_id>"],
          "rating": "number with one decimal, or null"
        }
      }
    }
  }
}
```

A `todo_completion` week that has To-Dos due looks like this:

```json
{"due": 4, "done": 3, "rate_percent": 75, "meets_target": false}
```

`meets_target` compares the exact ratio with 90%, not the rounded percent.
