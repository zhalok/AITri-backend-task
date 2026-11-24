from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class PersonOut(BaseModel):
    id: str
    name: str


class MeasurableStatusOut(BaseModel):
    measurable_id: str
    name: str
    unit: str
    goal_type: str
    goal_value: Decimal | None
    goal_min: Decimal | None
    goal_max: Decimal | None
    score: Decimal | None
    status: str


class SolvedIssueOut(BaseModel):
    id: str
    title: str
    owner_id: str
    solved_at: datetime | None
    resolution_note: str | None


class CreatedTodoOut(BaseModel):
    id: str
    title: str
    owner_id: str
    due_date: date
    done_at: datetime | None
    source_issue_id: str | None


class RatingSummaryOut(BaseModel):
    average: float | None
    count: int
    by_user: dict[str, int]


class MeetingSummaryOut(BaseModel):
    meeting_id: str
    team_id: str
    facilitator_id: str
    started_at: datetime
    ended_at: datetime
    attendees: list[PersonOut]
    rating: RatingSummaryOut
    week_start: date  # the last closed week as of the meeting
    measurables: list[MeasurableStatusOut]
    issues_solved: list[SolvedIssueOut]
    todos_created: list[CreatedTodoOut]
