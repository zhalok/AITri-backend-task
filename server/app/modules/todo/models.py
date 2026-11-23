from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Todo(Base):
    __tablename__ = "todos"
    __table_args__ = (CheckConstraint("length(btrim(title)) > 0", name="ck_todo_title_not_blank"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(300))
    due_date: Mapped[date] = mapped_column(Date)  # calendar date in company time
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_issue_id: Mapped[str | None] = mapped_column(ForeignKey("issues.id"), index=True)
    created_in_meeting_id: Mapped[str | None] = mapped_column(ForeignKey("meetings.id"))
