from dataclasses import dataclass
from datetime import datetime

from app.core.base import BaseService, new_id
from app.core.clock import Clock
from app.core.errors import ConflictError, DomainValidationError, ForbiddenError
from app.modules.meeting.models import SECTION_MINUTES, SECTION_ORDER, Meeting, Section
from app.modules.meeting.repository import MeetingRepository
from app.modules.user.models import User


@dataclass
class MeetingState:
    """Everything a client needs to render a meeting. The controller turns it into the response."""

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


class MeetingService(BaseService[Meeting]):
    entity_name = "Meeting"
    repository: MeetingRepository

    def __init__(self, repository: MeetingRepository, clock: Clock):
        super().__init__(repository)
        self.clock = clock

    def get_active_for_team(self, team_id: str) -> Meeting | None:
        return self.repository.get_active_for_team(team_id)

    def start(self, team_id: str, facilitator: User) -> Meeting:
        now = self.clock.now()
        meeting = Meeting(
            id=new_id(), team_id=team_id, facilitator_id=facilitator.id,
            started_at=now, current_section=Section.SCORECARD, section_started_at=now,
        )
        self.repository.add_meeting(meeting)
        self.repository.add_attendee(meeting.id, facilitator.id)
        return meeting

    def join(self, meeting: Meeting, user: User) -> None:
        self._require_active(meeting)
        self.repository.add_attendee(meeting.id, user.id)

    def require_facilitator(self, meeting: Meeting, user: User) -> None:
        if meeting.facilitator_id != user.id:
            raise ForbiddenError("Only the facilitator can do this")

    def advance(self, meeting: Meeting) -> Meeting:
        """Facilitator may advance at any time, even when over time. Never advances automatically."""
        self._require_active(meeting)
        idx = SECTION_ORDER.index(Section(meeting.current_section))
        if idx == len(SECTION_ORDER) - 1:
            raise ConflictError("Already in the last section; end the meeting instead")
        meeting.current_section = SECTION_ORDER[idx + 1]
        meeting.section_started_at = self.clock.now()
        self.repository.save()
        return meeting

    def end(self, meeting: Meeting) -> Meeting:
        self._require_active(meeting)
        meeting.ended_at = self.clock.now()
        self.repository.save()
        return meeting

    def rate(self, meeting: Meeting, user: User, rating: int) -> None:
        self._require_active(meeting)
        if meeting.current_section != Section.CONCLUDE:
            raise ConflictError("Ratings open in the Conclude section")
        if user.id not in self.repository.attendee_ids(meeting.id):
            raise ForbiddenError("Only attendees can rate")
        self.repository.upsert_rating(meeting.id, user.id, rating)

    def state(self, meeting: Meeting) -> MeetingState:
        """Everything a client needs to render the meeting. The server owns the timer."""
        end = meeting.ended_at or self.clock.now()
        elapsed = max(0, int((end - meeting.section_started_at).total_seconds()))
        duration = SECTION_MINUTES[Section(meeting.current_section)] * 60
        ratings = self.repository.ratings(meeting.id)
        avg = None
        if ratings:  # round half up to one decimal
            n = len(ratings)
            avg = ((20 * sum(ratings.values()) + n) // (2 * n)) / 10
        return MeetingState(
            id=meeting.id, team_id=meeting.team_id, facilitator_id=meeting.facilitator_id,
            started_at=meeting.started_at, ended_at=meeting.ended_at,
            current_section=meeting.current_section, section_started_at=meeting.section_started_at,
            section_duration_seconds=duration, section_elapsed_seconds=elapsed, over_time=elapsed > duration,
            attendee_ids=self.repository.attendee_ids(meeting.id), ratings=ratings, average_rating=avg,
        )

    @staticmethod
    def _require_active(meeting: Meeting) -> None:
        if not meeting.is_active:
            raise DomainValidationError("Meeting has ended")
