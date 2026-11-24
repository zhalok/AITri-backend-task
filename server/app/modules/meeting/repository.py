from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from app.core.base import BaseRepository
from app.core.errors import ConflictError
from app.modules.meeting.models import Meeting, MeetingAttendee, MeetingRating, MeetingSection, MeetingStatus


class MeetingRepository(BaseRepository[Meeting]):
    model = Meeting

    def add_meeting(self, meeting: Meeting) -> Meeting:
        try:
            with self.session.begin_nested():
                return self.add(meeting)
        except IntegrityError as exc:  # uq_one_active_meeting_per_team
            raise ConflictError("This team already has an active meeting") from exc

    def get_active_for_team(self, team_id: str) -> Meeting | None:
        stmt = select(Meeting).where(Meeting.team_id == team_id, Meeting.status == MeetingStatus.ACTIVE)
        return self.session.scalars(stmt).first()

    def save(self) -> None:
        self.session.flush()

    def add_attendee(self, meeting_id: str, user_id: str) -> None:
        stmt = insert(MeetingAttendee).values(meeting_id=meeting_id, user_id=user_id).on_conflict_do_nothing()
        self.session.execute(stmt)

    def remove_attendee(self, meeting_id: str, user_id: str) -> None:
        # A rating belongs to an attendee (foreign key), so it goes with them.
        self.session.execute(delete(MeetingRating).where(MeetingRating.meeting_id == meeting_id, MeetingRating.user_id == user_id))
        self.session.execute(delete(MeetingAttendee).where(MeetingAttendee.meeting_id == meeting_id, MeetingAttendee.user_id == user_id))

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

    def open_section(self, meeting_id: str, section: str, at: datetime) -> None:
        self.session.add(MeetingSection(meeting_id=meeting_id, section=section, started_at=at))
        self.session.flush()

    def close_open_section(self, meeting_id: str, at: datetime) -> None:
        stmt = (
            update(MeetingSection)
            .where(MeetingSection.meeting_id == meeting_id, MeetingSection.ended_at.is_(None))
            .values(ended_at=at)
        )
        self.session.execute(stmt)

    def sections(self, meeting_id: str) -> list[MeetingSection]:
        stmt = select(MeetingSection).where(MeetingSection.meeting_id == meeting_id).order_by(MeetingSection.started_at)
        return list(self.session.scalars(stmt))
