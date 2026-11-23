from datetime import date

from pydantic import BaseModel, ConfigDict


class MilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    rock_id: str
    title: str
    due_date: date
    done: bool
