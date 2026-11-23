from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Response

from app.core.auth import get_current_user
from app.modules.issue.factory import get_issue_usecase
from app.modules.issue.schemas import IssueCreate, IssueOut, IssuePriorityUpdate, IssueSolve
from app.modules.issue.usecase import IssueUseCase
from app.modules.user.models import User

router = APIRouter(tags=["issues"])


@router.get("/teams/{team_id}/issues", response_model=list[IssueOut])
def list_issues(
    team_id: str,
    status: Literal["unsolved", "solved"] = "unsolved",
    actor: User = Depends(get_current_user),
    uc: IssueUseCase = Depends(get_issue_usecase),
):
    return uc.list_issues(actor, team_id, solved=status == "solved")


@router.post("/teams/{team_id}/issues", response_model=IssueOut, status_code=201)
def create_issue(
    team_id: str, body: IssueCreate, actor: User = Depends(get_current_user), uc: IssueUseCase = Depends(get_issue_usecase)
):
    return uc.create(actor, team_id, body.title, body.priority)


@router.patch("/issues/{issue_id}/priority", response_model=IssueOut)
def set_priority(
    issue_id: str, body: IssuePriorityUpdate, actor: User = Depends(get_current_user), uc: IssueUseCase = Depends(get_issue_usecase)
):
    return uc.set_priority(actor, issue_id, body.priority)


@router.post("/issues/{issue_id}/solve", response_model=IssueOut)
def solve_issue(
    issue_id: str, body: IssueSolve, actor: User = Depends(get_current_user), uc: IssueUseCase = Depends(get_issue_usecase)
):
    return uc.solve(actor, issue_id, body.note)


@router.post("/measurables/{measurable_id}/scores/{week_start}/issue", response_model=IssueOut)
def make_it_an_issue(
    measurable_id: str,
    week_start: date,
    response: Response,
    actor: User = Depends(get_current_user),
    uc: IssueUseCase = Depends(get_issue_usecase),
):
    """Creates the Issue (201) or returns the existing unsolved one (200)."""
    issue, created = uc.make_it_an_issue(actor, measurable_id, week_start)
    response.status_code = 201 if created else 200
    return issue
