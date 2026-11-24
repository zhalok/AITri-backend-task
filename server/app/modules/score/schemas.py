from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.measurable.schemas import MeasurableOut


class ScoreIn(BaseModel):
    value: Decimal = Field(allow_inf_nan=False, max_digits=18, decimal_places=4)
    # The score the editor was looking at (null = an empty cell). Omit it and the last save wins; send it and
    # the save is refused with 409 if someone changed the cell meanwhile.
    seen: Decimal | None = Field(default=None, allow_inf_nan=False, max_digits=18, decimal_places=4)


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    measurable_id: str
    week_start: date
    value: Decimal


class ScorecardRow(BaseModel):
    measurable: MeasurableOut
    scores: dict[date, Decimal | None]
    statuses: dict[date, str]


class ScorecardOut(BaseModel):
    weeks: list[date]
    rows: list[ScorecardRow]

    @classmethod
    def from_scorecard(cls, card) -> "ScorecardOut":
        rows = [ScorecardRow(measurable=l.measurable, scores=l.scores, statuses=l.statuses) for l in card.lines]
        return cls(weeks=card.weeks, rows=rows)
