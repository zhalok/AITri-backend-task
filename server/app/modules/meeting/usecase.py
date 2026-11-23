from app.modules.meeting.schemas import MeetingStateOut
from app.modules.meeting.service import MeetingService
from app.core.permissions import Action
from app.core.rbac import Rbac
from app.modules.team.scope import TeamScope
from app.modules.user.models import User


class MeetingUseCase:
    def __init__(self, meetings: MeetingService, rbac: Rbac, scope: TeamScope):
        self.meetings = meetings
        self.rbac = rbac
        self.scope = scope

    def start(self, actor: User, team_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.START_MEETING)
        self.scope.require_member(actor, team_id)
        return self.meetings.state(self.meetings.start(team_id, actor))  # the starter becomes facilitator

    def admin_start(self, actor: User, team_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.ANY_TEAM_START_MEETING)
        return self.meetings.state(self.meetings.start(team_id, actor))

    def get(self, actor: User, meeting_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.VIEW_MEETING)
        meeting = self.meetings.get_or_raise(meeting_id)
        self.scope.require_member(actor, meeting.team_id)
        return self.meetings.state(meeting)

    def admin_get(self, actor: User, meeting_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.ANY_TEAM_VIEW_MEETING)
        return self.meetings.state(self.meetings.get_or_raise(meeting_id))

    def get_active(self, actor: User, team_id: str) -> MeetingStateOut | None:
        self.rbac.require(actor, Action.VIEW_ACTIVE_MEETING)
        self.scope.require_member(actor, team_id)
        return self._active_state(team_id)

    def admin_get_active(self, actor: User, team_id: str) -> MeetingStateOut | None:
        self.rbac.require(actor, Action.ANY_TEAM_VIEW_ACTIVE_MEETING)
        return self._active_state(team_id)

    def join(self, actor: User, meeting_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.JOIN_MEETING)  # Observers may join
        meeting = self.meetings.get_or_raise(meeting_id)
        self.scope.require_member(actor, meeting.team_id)
        return self._join(actor, meeting)

    def admin_join(self, actor: User, meeting_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.ANY_TEAM_JOIN_MEETING)
        return self._join(actor, self.meetings.get_or_raise(meeting_id))

    def advance(self, actor: User, meeting_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.ADVANCE_MEETING)
        meeting = self.meetings.get_or_raise(meeting_id)
        self.scope.require_member(actor, meeting.team_id)
        return self._advance(actor, meeting)

    def admin_advance(self, actor: User, meeting_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.ANY_TEAM_ADVANCE_MEETING)
        return self._advance(actor, self.meetings.get_or_raise(meeting_id))

    def end(self, actor: User, meeting_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.END_MEETING)
        meeting = self.meetings.get_or_raise(meeting_id)
        self.scope.require_member(actor, meeting.team_id)
        return self._end(actor, meeting)

    def admin_end(self, actor: User, meeting_id: str) -> MeetingStateOut:
        self.rbac.require(actor, Action.ANY_TEAM_END_MEETING)
        return self._end(actor, self.meetings.get_or_raise(meeting_id))

    def rate(self, actor: User, meeting_id: str, rating: int) -> MeetingStateOut:
        self.rbac.require(actor, Action.RATE_MEETING)
        meeting = self.meetings.get_or_raise(meeting_id)
        self.scope.require_member(actor, meeting.team_id)
        return self._rate(actor, meeting, rating)

    def admin_rate(self, actor: User, meeting_id: str, rating: int) -> MeetingStateOut:
        self.rbac.require(actor, Action.ANY_TEAM_RATE_MEETING)
        return self._rate(actor, self.meetings.get_or_raise(meeting_id), rating)

    # Meeting-specific rules (facilitator-only, attendee-only) apply on both the narrow and wide path.
    def _active_state(self, team_id: str) -> MeetingStateOut | None:
        meeting = self.meetings.get_active_for_team(team_id)
        return self.meetings.state(meeting) if meeting else None

    def _join(self, actor: User, meeting) -> MeetingStateOut:
        self.meetings.join(meeting, actor)
        return self.meetings.state(meeting)

    def _advance(self, actor: User, meeting) -> MeetingStateOut:
        self.meetings.require_facilitator(meeting, actor)
        return self.meetings.state(self.meetings.advance(meeting))

    def _end(self, actor: User, meeting) -> MeetingStateOut:
        self.meetings.require_facilitator(meeting, actor)
        return self.meetings.state(self.meetings.end(meeting))

    def _rate(self, actor: User, meeting, rating: int) -> MeetingStateOut:
        self.meetings.rate(meeting, actor, rating)
        return self.meetings.state(meeting)
