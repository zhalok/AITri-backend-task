from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.meeting_summary.factory import get_meeting_summary_usecase
from app.modules.meeting_summary.schemas import MeetingSummaryOut
from app.modules.meeting_summary.usecase import MeetingSummaryUseCase
from app.modules.user.models import User

router = APIRouter(tags=["meetings"])


@router.get("/meetings/{meeting_id}/summary", response_model=MeetingSummaryOut)
def get_summary(
    meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingSummaryUseCase = Depends(get_meeting_summary_usecase)
):
    """Any ended meeting (409 while it is still running): last closed week's Measurable statuses,
    Issues solved, To-Dos created, attendees and the rating."""
    return uc.get(actor, meeting_id)


admin_router = APIRouter(prefix="/admin", tags=["admin: any team"])


@admin_router.get("/meetings/{meeting_id}/summary", response_model=MeetingSummaryOut)
def admin_get_summary(
    meeting_id: str, actor: User = Depends(get_current_user), uc: MeetingSummaryUseCase = Depends(get_meeting_summary_usecase)
):
    return uc.admin_get(actor, meeting_id)
