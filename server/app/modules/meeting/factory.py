from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, get_clock
from app.core.database import get_session
from app.modules.meeting.repository import MeetingRepository
from app.modules.meeting.service import MeetingService
from app.modules.meeting.usecase import MeetingUseCase
from app.modules.team.factory import get_access_policy
from app.modules.team.policy import AccessPolicy


def get_meeting_repository(session: Session = Depends(get_session)) -> MeetingRepository:
    return MeetingRepository(session)


def get_meeting_service(
    repo: MeetingRepository = Depends(get_meeting_repository), clock: Clock = Depends(get_clock)
) -> MeetingService:
    return MeetingService(repo, clock)


def get_meeting_usecase(
    meetings: MeetingService = Depends(get_meeting_service), policy: AccessPolicy = Depends(get_access_policy)
) -> MeetingUseCase:
    return MeetingUseCase(meetings, policy)
