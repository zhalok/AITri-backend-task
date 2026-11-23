from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.measurable.repository import MeasurableRepository
from app.modules.measurable.service import MeasurableService
from app.modules.measurable.usecase import MeasurableUseCase
from app.modules.team.factory import get_team_scope
from app.core.rbac import Rbac, get_rbac
from app.modules.team.scope import TeamScope


def get_measurable_repository(session: Session = Depends(get_session)) -> MeasurableRepository:
    return MeasurableRepository(session)


def get_measurable_service(repo: MeasurableRepository = Depends(get_measurable_repository)) -> MeasurableService:
    return MeasurableService(repo)


def get_measurable_usecase(
    measurables: MeasurableService = Depends(get_measurable_service),
    rbac: Rbac = Depends(get_rbac), scope: TeamScope = Depends(get_team_scope),
) -> MeasurableUseCase:
    return MeasurableUseCase(measurables, rbac, scope)
