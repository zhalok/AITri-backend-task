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
    # The priority the editor was looking at (null = none). Omit it and the last save wins; send it and the
    # change is refused with 409 if someone else changed the priority meanwhile.
    seen: Priority | None = None


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
    solved_at: datetime | None
    resolution_note: str | None
    source_measurable_id: str | None
    source_week_start: date | None
    solved_in_meeting_id: str | None
