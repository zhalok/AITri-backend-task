import { ArrowRight, Flag, ShieldAlert } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { AgendaTimer } from '@/components/meeting/AgendaTimer'
import { Attendees } from '@/components/meeting/Attendees'
import { ConcludeView } from '@/components/meeting/ConcludeView'
import { MeetingSummary } from '@/components/meeting/MeetingSummary'
import { StartMeetingButton } from '@/components/meeting/StartMeetingButton'
import IssuesSection from '@/components/IssuesSection'
import ScorecardSection from '@/components/ScorecardSection'
import { Empty, LoadingRows } from '@/components/SectionCard'
import TodosSection from '@/components/TodosSection'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  useActiveMeeting, useAdvanceMeeting, useEndMeeting, useJoinMeeting, useMeeting, useMembers, useTeams,
} from '@/hooks/queries'
import { useTeamSocket } from '@/hooks/useTeamSocket'
import { ApiError } from '@/lib/api'
import { SECTION_LABEL } from '@/lib/format'

export default function MeetingPage() {
  const { teamId = '', meetingId } = useParams()
  useTeamSocket(teamId) // same live feed as the Team page: edits made on either page reach both
  return meetingId ? <MeetingRoom teamId={teamId} meetingId={meetingId} /> : <FindMeeting teamId={teamId} />
}

/** /teams/:id/meeting with no meeting id: go to the active meeting, or offer to start one. */
function FindMeeting({ teamId }: { teamId: string }) {
  const active = useActiveMeeting(teamId)
  if (active.isLoading) return <LoadingRows />
  if (active.data) return <Navigate to={`/teams/${teamId}/meeting/${active.data.id}`} replace />
  return (
    <div className="flex flex-col items-center gap-3 py-24 text-center">
      <Empty>This team has no meeting running.</Empty>
      <StartMeetingButton teamId={teamId} />
    </div>
  )
}

function MeetingRoom({ teamId, meetingId }: { teamId: string; meetingId: string }) {
  const { user } = useAuth()
  const teams = useTeams()
  const members = useMembers(teamId)
  const query = useMeeting(teamId, meetingId)
  const meeting = query.data
  const join = useJoinMeeting(teamId)
  const advance = useAdvanceMeeting(teamId)
  const end = useEndMeeting(teamId)
  const joined = useRef(false)

  // Anyone who can read the team may join. Opening the page is joining; refreshing is a no-op.
  useEffect(() => {
    if (!meeting || meeting.ended_at || !user || joined.current) return
    if (!meeting.attendee_ids.includes(user.id)) {
      joined.current = true
      join.mutate(meeting.id)
    }
  }, [meeting, user, join])

  if (query.error instanceof ApiError && [403, 404].includes(query.error.status)) {
    return (
      <div className="flex flex-col items-center gap-2 py-24 text-center">
        <ShieldAlert className="size-8 text-muted-foreground" />
        <h1 className="text-lg font-semibold">You can't open this meeting</h1>
        <p className="text-sm text-muted-foreground">{query.error.message}</p>
      </div>
    )
  }
  if (!meeting) return <LoadingRows />

  const ended = !!meeting.ended_at
  const isFacilitator = user?.id === meeting.facilitator_id
  const facilitator = members.data?.find((u) => u.id === meeting.facilitator_id)?.name ?? meeting.facilitator_id
  const section = meeting.current_section

  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold tracking-tight">
          {teams.data?.find((t) => t.id === teamId)?.name ?? 'Team'} · Level 10 Meeting
        </h1>
        <Badge variant={ended ? 'secondary' : 'default'}>{ended ? 'Ended' : SECTION_LABEL[section]}</Badge>
        <span className="text-sm text-muted-foreground">Facilitator: {facilitator}</span>
        {isFacilitator && !ended && (
          <div className="ml-auto flex gap-2">
            {section !== 'conclude' && (
              <Button disabled={advance.isPending} onClick={() => advance.mutate(meeting.id)}>
                Next section <ArrowRight />
              </Button>
            )}
            <Button
              variant={section === 'conclude' ? 'default' : 'outline'} disabled={end.isPending}
              onClick={() => { if (confirm('End the meeting for everyone?')) end.mutate(meeting.id) }}
            >
              <Flag /> End meeting
            </Button>
          </div>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
        <aside className="space-y-4">
          <AgendaTimer meeting={meeting} receivedAt={query.dataUpdatedAt} />
          <Attendees teamId={teamId} meeting={meeting} />
        </aside>
        <div className="min-w-0 space-y-4">
          {ended && <MeetingSummary teamId={teamId} meeting={meeting} />}
          {!ended && section === 'scorecard' && <ScorecardSection teamId={teamId} />}
          {!ended && section === 'ids' && (
            <div className="grid gap-4 xl:grid-cols-2">
              <IssuesSection teamId={teamId} />
              <TodosSection teamId={teamId} />
            </div>
          )}
          {!ended && section === 'conclude' && <ConcludeView teamId={teamId} meeting={meeting} />}
        </div>
      </div>
    </>
  )
}
