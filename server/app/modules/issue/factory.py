from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, get_clock
from app.core.database import get_session
from app.modules.issue.repository import IssueRepository
from app.modules.issue.service import IssueService
from app.modules.issue.usecase import IssueUseCase
from app.modules.measurable.factory import get_measurable_service
from app.modules.measurable.service import MeasurableService
from app.modules.meeting.factory import get_meeting_service
from app.modules.meeting.service import MeetingService
from app.modules.score.factory import get_score_service
from app.modules.score.service import ScoreService
from app.modules.team.factory import get_team_scope
from app.core.rbac import Rbac, get_rbac
from app.modules.team.scope import TeamScope


def get_issue_repository(session: Session = Depends(get_session)) -> IssueRepository:
    return IssueRepository(session)


def get_issue_service(repo: IssueRepository = Depends(get_issue_repository), clock: Clock = Depends(get_clock)) -> IssueService:
    return IssueService(repo, clock)


def get_issue_usecase(
    issues: IssueService = Depends(get_issue_service),
    measurables: MeasurableService = Depends(get_measurable_service),
    meetings: MeetingService = Depends(get_meeting_service),
    scores: ScoreService = Depends(get_score_service),
    rbac: Rbac = Depends(get_rbac), scope: TeamScope = Depends(get_team_scope),

) -> IssueUseCase:
    return IssueUseCase(issues, measurables, meetings, scores, rbac, scope)
