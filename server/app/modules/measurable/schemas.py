from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MeasurableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    team_id: str
    owner_id: str
    name: str
    unit: str
    goal_type: str
    goal_value: Decimal | None
    goal_min: Decimal | None
    goal_max: Decimal | None
