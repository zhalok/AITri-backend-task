from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class TodoCreate(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    owner_id: str


class CompletionRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    week_start: date
    due: int
    done: int
    rate: int | None
    meets_target: bool | None
    target: int = 90


class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    team_id: str
    owner_id: str
    title: str
    due_date: date
    done_at: datetime | None
    created_at: datetime
    source_issue_id: str | None
    created_in_meeting_id: str | None
    is_overdue: bool = False

    @classmethod
    def from_view(cls, view) -> "TodoOut":
        out = cls.model_validate(view.todo)
        out.is_overdue = view.is_overdue
        return out
