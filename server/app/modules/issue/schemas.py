from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
Priority = Annotated[int, Field(ge=1, le=5)]


class IssueCreate(BaseModel):
    title: Title
    priority: Priority | None = None


class IssuePriorityUpdate(BaseModel):
    priority: Priority | None


class IssueSolve(BaseModel):
    note: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    team_id: str
    owner_id: str
    title: str
    priority: int | None
    created_at: datetime
    # maybe we can have an uniqueness check on 
    # solved_at, source_week_start and source_measurable_id
    solved_at: datetime | None
    resolution_note: str | None
    source_measurable_id: str | None
    source_week_start: date | None
    solved_in_meeting_id: str | None
