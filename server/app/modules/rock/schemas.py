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
    progress: int
    milestones: list[MilestoneOut]

    @classmethod
    def from_detail(cls, detail) -> "RockOut":
        r = detail.rock
        return cls(
            id=r.id, team_id=r.team_id, owner_id=r.owner_id, title=r.title,
            quarter=r.quarter, status=detail.status, progress=detail.progress, milestones=detail.milestones,
        )
