from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from app.core.base import BaseRepository
from app.core.errors import ConflictError
from app.modules.meeting.models import Meeting, MeetingAttendee, MeetingRating


class MeetingRepository(BaseRepository[Meeting]):
    model = Meeting

    def add_meeting(self, meeting: Meeting) -> Meeting:
        try:
            with self.session.begin_nested():
                return self.add(meeting)
        except IntegrityError as exc:  # uq_one_active_meeting_per_team
            raise ConflictError("This team already has an active meeting") from exc

    def get_active_for_team(self, team_id: str) -> Meeting | None:
        stmt = select(Meeting).where(Meeting.team_id == team_id, Meeting.ended_at.is_(None))
        return self.session.scalars(stmt).first()

    def save(self) -> None:
        self.session.flush()

    def add_attendee(self, meeting_id: str, user_id: str) -> None:
        stmt = insert(MeetingAttendee).values(meeting_id=meeting_id, user_id=user_id).on_conflict_do_nothing()
        self.session.execute(stmt)

    def attendee_ids(self, meeting_id: str) -> list[str]:
        stmt = select(MeetingAttendee.user_id).where(MeetingAttendee.meeting_id == meeting_id).order_by(MeetingAttendee.user_id)
        return list(self.session.scalars(stmt))

    def upsert_rating(self, meeting_id: str, user_id: str, rating: int) -> None:
        stmt = (
            insert(MeetingRating)
            .values(meeting_id=meeting_id, user_id=user_id, rating=rating)
            .on_conflict_do_update(index_elements=["meeting_id", "user_id"], set_={"rating": rating})
        )
        self.session.execute(stmt)

    def ratings(self, meeting_id: str) -> dict[str, int]:
        stmt = select(MeetingRating).where(MeetingRating.meeting_id == meeting_id)
        return {r.user_id: r.rating for r in self.session.scalars(stmt)}
