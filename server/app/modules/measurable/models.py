from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Measurable(Base):
    __tablename__ = "measurables"
    __table_args__ = (
        CheckConstraint("goal_type in ('at_least','at_most','between','exactly')", name="ck_measurable_goal_type"),
        # Each goal type must carry exactly the numbers it needs.
        CheckConstraint(
            "(goal_type = 'between' and goal_min is not null and goal_max is not null and goal_min <= goal_max"
            " and goal_value is null)"
            " or (goal_type <> 'between' and goal_value is not null and goal_min is null and goal_max is null)",
            name="ck_measurable_goal_shape",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(32))
    goal_type: Mapped[str] = mapped_column(String(16))
    goal_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    goal_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    goal_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
