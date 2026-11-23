from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Section(StrEnum):
    SCORECARD = "scorecard"
    IDS = "ids"
    CONCLUDE = "conclude"


SECTION_ORDER = [Section.SCORECARD, Section.IDS, Section.CONCLUDE]
SECTION_MINUTES = {Section.SCORECARD: 5, Section.IDS: 60, Section.CONCLUDE: 10}


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (
        CheckConstraint("current_section in ('scorecard','ids','conclude')", name="ck_meeting_section"),
        CheckConstraint("ended_at is null or ended_at >= started_at", name="ck_meeting_end_after_start"),
        # One active meeting per team, enforced by the database.
        Index("uq_one_active_meeting_per_team", "team_id", unique=True, postgresql_where=text("ended_at is null")),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    facilitator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_section: Mapped[str] = mapped_column(String(16), default=Section.SCORECARD)
    section_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    @property
    def is_active(self) -> bool:
        return self.ended_at is None


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"

    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)


class MeetingRating(Base):
    __tablename__ = "meeting_ratings"
    __table_args__ = (
        CheckConstraint("rating between 1 and 10", name="ck_rating_range"),
        # Only attendees can rate.
        ForeignKeyConstraint(
            ["meeting_id", "user_id"], ["meeting_attendees.meeting_id", "meeting_attendees.user_id"]
        ),
    )

    meeting_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer)
