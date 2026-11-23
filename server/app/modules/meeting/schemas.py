from datetime import datetime

from pydantic import BaseModel, Field


class RatingIn(BaseModel):
    rating: int = Field(ge=1, le=10)


class MeetingStateOut(BaseModel):
    id: str
    team_id: str
    facilitator_id: str
    started_at: datetime
    ended_at: datetime | None
    current_section: str
    section_started_at: datetime
    section_duration_seconds: int
    section_elapsed_seconds: int
    over_time: bool
    attendee_ids: list[str]
    ratings: dict[str, int]
    average_rating: float | None
