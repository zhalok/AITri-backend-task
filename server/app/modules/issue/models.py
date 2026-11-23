from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Index, SmallInteger, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        CheckConstraint("priority is null or priority between 1 and 5", name="ck_issue_priority"),
        CheckConstraint("length(btrim(title)) > 0", name="ck_issue_title_not_blank"),
        # Solved <=> has a note and a timestamp.
        CheckConstraint(
            "(solved_at is null and resolution_note is null)"
            " or (solved_at is not null and resolution_note is not null and length(btrim(resolution_note)) > 0)",
            name="ck_issue_solved_has_note",
        ),
        # Source is a (Measurable, week) pair: both or neither.
        CheckConstraint(
            "(source_measurable_id is null) = (source_week_start is null)", name="ck_issue_source_pair"
        ),
        CheckConstraint(
            "source_week_start is null or extract(isodow from source_week_start) = 1", name="ck_issue_source_monday"
        ),
        # No duplicates: at most one UNSOLVED Issue per (Measurable, week). The race-proof guard.
        Index(
            "uq_issue_unsolved_per_source", "source_measurable_id", "source_week_start", unique=True,
            postgresql_where=text("solved_at is null and source_measurable_id is not null"),
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(300))
    priority: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    source_measurable_id: Mapped[str | None] = mapped_column(ForeignKey("measurables.id"))
    source_week_start: Mapped[date | None] = mapped_column(Date)
    solved_in_meeting_id: Mapped[str | None] = mapped_column(ForeignKey("meetings.id"))
