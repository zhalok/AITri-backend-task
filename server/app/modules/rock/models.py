from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Rock(Base):
    __tablename__ = "rocks"
    __table_args__ = (
        CheckConstraint("status in ('on_track','off_track','complete')", name="ck_rock_status"),
        CheckConstraint("quarter ~ '^[0-9]{4}-Q[1-4]$'", name="ck_rock_quarter"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    quarter: Mapped[str] = mapped_column(String(7))
    status: Mapped[str] = mapped_column(String(16))  # seeded status; effective status is computed
