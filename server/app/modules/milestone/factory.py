from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.milestone.repository import MilestoneRepository
from app.modules.milestone.service import MilestoneService


def get_milestone_repository(session: Session = Depends(get_session)) -> MilestoneRepository:
    return MilestoneRepository(session)


def get_milestone_service(repo: MilestoneRepository = Depends(get_milestone_repository)) -> MilestoneService:
    return MilestoneService(repo)
