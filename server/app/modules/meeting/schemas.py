from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RatingIn(BaseModel):
    rating: int = Field(ge=1, le=10)


class MeetingSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section: str
    started_at: datetime
    ended_at: datetime | None


class MeetingStateOut(BaseModel):
    id: str
    team_id: str
    facilitator_id: str
    started_at: datetime
    ended_at: datetime | None
    status: str
    current_section: str
    section_started_at: datetime
    section_duration_seconds: int
    section_elapsed_seconds: int
    over_time: bool
    attendee_ids: list[str]
    ratings: dict[str, int]
    average_rating: float | None
    sections: list[MeetingSectionOut] = []
