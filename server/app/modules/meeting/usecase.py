from app.modules.meeting.schemas import MeetingStateOut
from app.modules.meeting.service import MeetingService
from app.modules.team.policy import AccessPolicy
from app.modules.user.models import User


class MeetingUseCase:
    def __init__(self, meetings: MeetingService, policy: AccessPolicy):
        self.meetings = meetings
        self.policy = policy

    def start(self, actor: User, team_id: str) -> MeetingStateOut:
        self.policy.require_write(actor, team_id)  # Admin or Team Member; becomes facilitator
        return self.meetings.state(self.meetings.start(team_id, actor))

    def get(self, actor: User, meeting_id: str) -> MeetingStateOut:
        meeting = self.meetings.get_or_raise(meeting_id)
        self.policy.require_read(actor, meeting.team_id)
        return self.meetings.state(meeting)

    def get_active(self, actor: User, team_id: str) -> MeetingStateOut | None:
        self.policy.require_read(actor, team_id)
        meeting = self.meetings.get_active_for_team(team_id)
        return self.meetings.state(meeting) if meeting else None

    def join(self, actor: User, meeting_id: str) -> MeetingStateOut:
        meeting = self.meetings.get_or_raise(meeting_id)
        self.policy.require_read(actor, meeting.team_id)  # Observers may join
        self.meetings.join(meeting, actor)
        return self.meetings.state(meeting)

    def advance(self, actor: User, meeting_id: str) -> MeetingStateOut:
        meeting = self.meetings.get_or_raise(meeting_id)
        self.policy.require_write(actor, meeting.team_id)
        self.meetings.require_facilitator(meeting, actor)
        return self.meetings.state(self.meetings.advance(meeting))

    def end(self, actor: User, meeting_id: str) -> MeetingStateOut:
        meeting = self.meetings.get_or_raise(meeting_id)
        self.policy.require_write(actor, meeting.team_id)
        self.meetings.require_facilitator(meeting, actor)
        return self.meetings.state(self.meetings.end(meeting))

    def rate(self, actor: User, meeting_id: str, rating: int) -> MeetingStateOut:
        meeting = self.meetings.get_or_raise(meeting_id)
        self.policy.require_write(actor, meeting.team_id)
        self.meetings.rate(meeting, actor, rating)
        return self.meetings.state(meeting)
