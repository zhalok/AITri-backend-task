from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, get_clock
from app.core.database import get_session
from app.modules.meeting.repository import MeetingRepository
from app.modules.meeting.service import MeetingService
from app.modules.meeting.usecase import MeetingUseCase
from app.modules.team.factory import get_team_scope
from app.core.rbac import Rbac, get_rbac
from app.modules.team.scope import TeamScope


def get_meeting_repository(session: Session = Depends(get_session)) -> MeetingRepository:
    return MeetingRepository(session)


def get_meeting_service(
    repo: MeetingRepository = Depends(get_meeting_repository), clock: Clock = Depends(get_clock)
) -> MeetingService:
    return MeetingService(repo, clock)


def get_meeting_usecase(
    meetings: MeetingService = Depends(get_meeting_service), rbac: Rbac = Depends(get_rbac), scope: TeamScope = Depends(get_team_scope)
) -> MeetingUseCase:
    return MeetingUseCase(meetings, rbac, scope)
