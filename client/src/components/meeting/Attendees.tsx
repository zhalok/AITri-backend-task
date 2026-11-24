import { SectionCard } from '@/components/SectionCard'
import { Badge } from '@/components/ui/badge'
import { useMembers } from '@/hooks/queries'
import type { MeetingState } from '@/lib/types'

export function Attendees({ teamId, meeting }: { teamId: string; meeting: MeetingState }) {
  const members = useMembers(teamId)
  const name = (id: string) => members.data?.find((u) => u.id === id)?.name ?? id
  return (
    <SectionCard title={`Attendees (${meeting.attendee_ids.length})`}>
      <ul className="space-y-1 text-sm">
        {meeting.attendee_ids.map((id) => (
          <li key={id} className="flex items-center gap-2">
            <span>{name(id)}</span>
            {id === meeting.facilitator_id && <Badge variant="secondary">Facilitator</Badge>}
          </li>
        ))}
      </ul>
    </SectionCard>
  )
}
