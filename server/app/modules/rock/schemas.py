from pydantic import BaseModel, ConfigDict

from app.modules.milestone.schemas import MilestoneOut


class RockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    team_id: str
    owner_id: str
    title: str
    quarter: str
    status: str
    milestones: list[MilestoneOut]
