"""The rules report: every computed value from brief 2.6, for the database as it stands, as JSON.

    python -m app.rules_report                    print it
    python -m app.rules_report --out rules_report.json
    docker compose exec api python -m app.rules_report

Run it on a freshly seeded database (what `docker compose up` gives you). "Now" comes from APP_NOW, so the same
command can be run at any date: every value is computed from the data and the clock, none is stored or
hard-coded. It connects to the database and calls the very same services and rule functions the API uses
(app/modules/*/rules.py), so the report and the app cannot disagree. Format: the root README.
"""
import argparse
import json
import sys
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.rbac import Rbac
from app.modules.issue.repository import IssueRepository
from app.modules.issue.service import IssueService
from app.modules.measurable.repository import MeasurableRepository
from app.modules.measurable.service import MeasurableService
from app.modules.meeting.repository import MeetingRepository
from app.modules.meeting.service import MeetingService
from app.modules.meeting_summary.usecase import MeetingSummaryUseCase
from app.modules.milestone.repository import MilestoneRepository
from app.modules.milestone.service import MilestoneService
from app.modules.rock.repository import RockRepository
from app.modules.rock.service import RockService
from app.modules.score.repository import ScoreRepository
from app.modules.score.service import ScoreService
from app.modules.team.models import Team
from app.modules.todo.repository import TodoRepository
from app.modules.todo.rules import completion_rate
from app.modules.todo.service import TodoService
from app.modules.user.repository import UserRepository
from app.modules.user.service import UserService


def _iso(d) -> str:
    return d.isoformat()


def build_report(session: Session, clock: Clock) -> dict:
    measurables = MeasurableService(MeasurableRepository(session))
    scores = ScoreService(ScoreRepository(session), clock)
    todos = TodoService(TodoRepository(session), clock)
    rocks = RockService(RockRepository(session), clock)
    milestones = MilestoneService(MilestoneRepository(session))
    issues = IssueService(IssueRepository(session), clock)
    meetings = MeetingService(MeetingRepository(session), clock)
    summaries = MeetingSummaryUseCase(
        meetings, issues, todos, measurables, scores, UserService(UserRepository(session)), Rbac(), None, clock,  # type: ignore[arg-type]
    )
    weeks = clock.last_n_weeks(13)  # oldest first, ending with the current week

    teams: dict[str, dict] = {}
    for team_id in session.scalars(select(Team.id).order_by(Team.id)):
        team_measurables = measurables.list_for_team(team_id)
        by_measurable = scores.scores_by_measurable([m.id for m in team_measurables], weeks)
        team_todos = todos.list_for_team(team_id)

        todo_completion = {}
        for week in weeks:
            rate = completion_rate(team_todos, week, clock.week_end(week))
            todo_completion[_iso(week)] = None if rate.rate is None else {
                "due": rate.due, "done": rate.done, "rate_percent": rate.rate, "meets_target": rate.meets_target,
            }

        current_rocks = rocks.list_current(team_id)
        milestones_by_rock = milestones.grouped_by_rock([r.id for r in current_rocks])
        rock_values = {}
        for rock in current_rocks:
            detail = rocks.detail(rock, milestones_by_rock.get(rock.id, []))
            rock_values[rock.id] = {"status": detail.status, "progress_percent": detail.progress}

        meeting_values = {}
        for meeting in meetings.list_ended_for_team(team_id):
            summary = summaries.build_summary(meeting)
            meeting_values[meeting.id] = {
                "scorecard_week": _iso(summary.week_start),
                "measurable_status": {m.measurable_id: m.status for m in sorted(summary.measurables, key=lambda m: m.measurable_id)},
                "issues_solved": sorted(i.id for i in summary.issues_solved),
                "todos_created": sorted(t.id for t in summary.todos_created),
                "attendee_ids": sorted(a.id for a in summary.attendees),
                "rating": summary.rating.average,
            }

        teams[team_id] = {
            "measurable_status": {
                m.id: {_iso(w): status for w, status in scores.statuses(m, {w: by_measurable[m.id].get(w) for w in weeks}).items()}
                for m in sorted(team_measurables, key=lambda m: m.id)
            },
            "todo_completion": todo_completion,
            "overdue_todos": sorted(t.id for t in team_todos if todos.is_overdue(t)),
            "rocks": dict(sorted(rock_values.items())),
            "issue_order": [i.id for i in issues.list_unsolved(team_id)],  # Issue order, not sorted by id
            "meetings": dict(sorted(meeting_values.items())),
        }

    return {"now": clock.now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"), "teams": teams}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Print every computed value from brief 2.6 as JSON.")
    parser.add_argument("--out", help="write the JSON to this file instead of printing it")
    args = parser.parse_args(argv)
    settings = get_settings()
    with SessionLocal() as session:
        report = build_report(session, Clock(settings.app_now, settings.company_timezone))
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
