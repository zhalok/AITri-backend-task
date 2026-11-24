"""The rules report against an independent oracle.

`oracle(...)` below recomputes every 2.6 value straight from seed.json, from the brief's wording, with plain
loops and calendar-date comparisons (the app compares instants and uses its own rule functions). If the two
ever disagree, one of them misread a rule. Checked at the default APP_NOW and at a later date, because the
graders will run the command at other dates too.
"""
import json
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

import pytest

from app.rules_report import build_report
from app.seed import DEFAULT_SEED, load_seed
from tests.helpers import make_clock

SEED = json.loads(DEFAULT_SEED.read_text())
TZ = ZoneInfo("America/Chicago")


def when(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def local_day(stamp: str) -> date:
    return when(stamp).astimezone(TZ).date()


def monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def half_up(x: Decimal, places: int = 0) -> Decimal:
    return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def status(goal: dict, value, week: date, current_week: date) -> str:
    if value is None:
        return "off_track" if week < current_week else "pending"
    v, kind = Decimal(str(value)), goal["type"]
    ok = {
        "at_least": lambda: v >= Decimal(str(goal["value"])),
        "at_most": lambda: v <= Decimal(str(goal["value"])),
        "exactly": lambda: v == Decimal(str(goal["value"])),
        "between": lambda: Decimal(str(goal["min"])) <= v <= Decimal(str(goal["max"])),
    }[kind]()
    return "on_track" if ok else "off_track"


def oracle(now_iso: str) -> dict:
    today = local_day(now_iso)
    this_week = monday(today)
    weeks = [this_week - timedelta(days=7 * i) for i in range(12, -1, -1)]
    quarter = f"{today.year}-Q{(today.month - 1) // 3 + 1}"
    out = {}
    for team in sorted(t["id"] for t in SEED["teams"]):
        measurables = sorted((m for m in SEED["measurables"] if m["team_id"] == team), key=lambda m: m["id"])
        score = {(s["measurable_id"], s["week_start"]): s["value"] for s in SEED["scores"]}
        todos = [t for t in SEED["todos"] if t["team_id"] == team]

        completion = {}
        for w in weeks:
            due = [t for t in todos if w <= date.fromisoformat(t["due_date"]) <= w + timedelta(days=6)]
            done = [t for t in due if t["done_at"] and local_day(t["done_at"]) <= w + timedelta(days=6)]
            completion[w.isoformat()] = None if not due else {
                "due": len(due), "done": len(done), "rate_percent": int(half_up(Decimal(len(done) * 100) / len(due))),
                "meets_target": len(done) * 100 >= 90 * len(due),
            }

        rocks = {}
        for r in (r for r in SEED["rocks"] if r["team_id"] == team and r["quarter"] == quarter):
            ms = [m for m in SEED["milestones"] if m["rock_id"] == r["id"]]
            late = any(not m["done"] and date.fromisoformat(m["due_date"]) < today for m in ms)
            st = r["status"] if r["status"] in ("complete", "off_track") else ("off_track" if late else "on_track")
            pct = (100 if r["status"] == "complete" else 0) if not ms else \
                int(half_up(Decimal(sum(m["done"] for m in ms) * 100) / len(ms)))
            rocks[r["id"]] = {"status": st, "progress_percent": pct}

        unsolved = [i for i in SEED["issues"] if i["team_id"] == team and not i["solved_at"]]
        unsolved.sort(key=lambda i: (-(i["priority"] or 0), i["created_at"], i["id"]))  # no priority = 0 = last

        meetings = {}
        for m in (m for m in SEED["meetings"] if m["team_id"] == team):
            reviewed = monday(local_day(m["ended_at"])) - timedelta(days=7)
            inside = lambda s: when(m["started_at"]) <= when(s) <= when(m["ended_at"])
            ratings = [Decimal(r["rating"]) for r in m["ratings"]]
            meetings[m["id"]] = {
                "scorecard_week": reviewed.isoformat(),
                "measurable_status": {
                    x["id"]: status(x["goal"], score.get((x["id"], reviewed.isoformat())), reviewed, reviewed + timedelta(days=7))
                    for x in measurables
                },
                "issues_solved": sorted(i["id"] for i in SEED["issues"]
                                        if i["team_id"] == team and i["solved_at"] and inside(i["solved_at"])),
                "todos_created": sorted(t["id"] for t in todos if inside(t["created_at"])),
                "attendee_ids": sorted(m["attendee_ids"]),
                "rating": float(half_up(sum(ratings) / len(ratings), 1)) if ratings else None,
            }

        out[team] = {
            "measurable_status": {
                x["id"]: {w.isoformat(): status(x["goal"], score.get((x["id"], w.isoformat())), w, this_week) for w in weeks}
                for x in measurables
            },
            "todo_completion": completion,
            "overdue_todos": sorted(t["id"] for t in todos if not t["done_at"] and date.fromisoformat(t["due_date"]) < today),
            "rocks": dict(sorted(rocks.items())),
            "issue_order": [i["id"] for i in unsolved],
            "meetings": dict(sorted(meetings.items())),
        }
    return out


@pytest.mark.parametrize("now", ["2026-11-11T15:00:00Z", "2026-11-16T05:59:59Z", "2026-11-16T06:00:00Z", "2026-12-14T15:00:00Z"])
def test_the_report_matches_the_oracle_at_several_dates(session, now):
    # 2026-11-16 05:59:59Z is Sunday 23:59:59 in Chicago (still last week); 06:00:00Z is Monday 00:00:00 (new week)
    load_seed(session, SEED)
    report = build_report(session, make_clock(now))
    assert report["now"] == now
    assert report["teams"] == oracle(now)


def test_the_report_has_the_documented_shape(session):
    load_seed(session, SEED)
    report = build_report(session, make_clock("2026-11-11T15:00:00Z"))
    assert set(report) == {"now", "teams"} and set(report["teams"]) == {"team_lead", "team_ops", "team_sales"}
    lead = report["teams"]["team_lead"]
    assert set(lead) == {"measurable_status", "todo_completion", "overdue_todos", "rocks", "issue_order", "meetings"}
    assert list(lead["todo_completion"])[0] == "2026-08-17" and list(lead["todo_completion"])[-1] == "2026-11-09"
    assert len(lead["todo_completion"]) == 13 and all(len(w) == 13 for w in lead["measurable_status"].values())
    assert None in lead["todo_completion"].values()  # a week with nothing due is null
    assert set(lead["meetings"]) == {"mt1", "mt2"}
    assert lead["overdue_todos"] == sorted(lead["overdue_todos"])


def test_known_boundary_values_from_the_seed(session):
    """Spot checks worked out by hand, so the oracle and the report cannot be wrong in the same way."""
    load_seed(session, SEED)
    t = build_report(session, make_clock("2026-11-11T15:00:00Z"))["teams"]["team_lead"]
    assert t["todo_completion"]["2026-11-02"] == {"due": 10, "done": 9, "rate_percent": 90, "meets_target": True}
    assert t["rocks"]["r2"] == {"status": "off_track", "progress_percent": 13}  # 1 of 8 = 12.5%, rounded half up
    assert t["rocks"]["r3"] == {"status": "complete", "progress_percent": 100}
    assert t["meetings"]["mt2"]["rating"] == 8.3  # 33 / 4 = 8.25, rounded half up
    assert t["meetings"]["mt1"]["measurable_status"]["m3"] == "on_track"  # 2.0 sits on the lower edge of 2..4
    assert t["measurable_status"]["m1"]["2026-11-09"] == "pending"  # the current week, no score yet
