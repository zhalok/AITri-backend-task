from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.meeting.factory import get_meeting_usecase
from app.modules.meeting.schemas import MeetingStateOut, RatingIn
from app.modules.meeting.usecase import MeetingUseCase
from app.modules.user.models import User

router = APIRouter(tags=["meetings"])


@router.post("/teams/{team_id}/meetings", response_model=MeetingStateOut, status_code=201)
def start_meeting(team_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.start(actor, team_id)


@router.get("/teams/{team_id}/meetings/active", response_model=MeetingStateOut | None)
def get_active_meeting(team_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.get_active(actor, team_id)


@router.get("/meetings/{meeting_id}", response_model=MeetingStateOut)
def get_meeting(meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.get(actor, meeting_id)


@router.post("/meetings/{meeting_id}/join", response_model=MeetingStateOut)
def join_meeting(meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.join(actor, meeting_id)


@router.post("/meetings/{meeting_id}/advance", response_model=MeetingStateOut)
def advance_meeting(meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.advance(actor, meeting_id)


@router.post("/meetings/{meeting_id}/end", response_model=MeetingStateOut)
def end_meeting(meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.end(actor, meeting_id)


@router.put("/meetings/{meeting_id}/rating", response_model=MeetingStateOut)
def rate_meeting(
    meeting_id: str, body: RatingIn, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)
):
    return uc.rate(actor, meeting_id, body.rating)


admin_router = APIRouter(prefix="/admin", tags=["admin: any team"])


@admin_router.post("/teams/{team_id}/meetings", response_model=MeetingStateOut, status_code=201)
def admin_start_meeting(team_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.admin_start(actor, team_id)


@admin_router.get("/teams/{team_id}/meetings/active", response_model=MeetingStateOut | None)
def admin_get_active_meeting(team_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.admin_get_active(actor, team_id)


@admin_router.get("/meetings/{meeting_id}", response_model=MeetingStateOut)
def admin_get_meeting(meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.admin_get(actor, meeting_id)


@admin_router.post("/meetings/{meeting_id}/join", response_model=MeetingStateOut)
def admin_join_meeting(meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.admin_join(actor, meeting_id)


@admin_router.post("/meetings/{meeting_id}/advance", response_model=MeetingStateOut)
def admin_advance_meeting(meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.admin_advance(actor, meeting_id)


@admin_router.post("/meetings/{meeting_id}/end", response_model=MeetingStateOut)
def admin_end_meeting(meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.admin_end(actor, meeting_id)


@admin_router.put("/meetings/{meeting_id}/rating", response_model=MeetingStateOut)
def admin_rate_meeting(meeting_id: str, body: RatingIn, actor: User = Depends(get_current_user), uc: MeetingUseCase = Depends(get_meeting_usecase)):
    return uc.admin_rate(actor, meeting_id, body.rating)
