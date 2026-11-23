from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        # ISODOW 1 = Monday: weeks are always identified by their Monday.
        CheckConstraint("extract(isodow from week_start) = 1", name="ck_score_week_is_monday"),
    )

    measurable_id: Mapped[str] = mapped_column(ForeignKey("measurables.id"), primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 4))
