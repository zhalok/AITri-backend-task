import { Empty, SectionCard } from '@/components/SectionCard'
import { useIssues, useMembers, useTodos } from '@/hooks/queries'
import { clockText, SECTION_LABEL } from '@/lib/format'
import type { MeetingState } from '@/lib/types'

/** What the team sees after the facilitator ends the meeting. */
export function MeetingSummary({ teamId, meeting }: { teamId: string; meeting: MeetingState }) {
  const members = useMembers(teamId)
  const solved = useIssues(teamId, 'solved')
  const todos = useTodos(teamId)
  const name = (id: string) => members.data?.find((u) => u.id === id)?.name ?? id
  const issues = (solved.data ?? []).filter((i) => i.solved_in_meeting_id === meeting.id)
  const created = (todos.data ?? []).filter((t) => t.created_in_meeting_id === meeting.id)

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <SectionCard title="Issues solved">
        {issues.length === 0 && <Empty>No Issues were solved.</Empty>}
        <ul className="divide-y text-sm">
          {issues.map((i) => (
            <li key={i.id} className="py-2">
              <div>{i.title}</div>
              <div className="text-xs text-muted-foreground">{i.resolution_note}</div>
            </li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="To-Dos created">
        {created.length === 0 && <Empty>No To-Dos were created.</Empty>}
        <ul className="divide-y text-sm">
          {created.map((t) => (
            <li key={t.id} className="flex justify-between gap-3 py-2">
              <span>{t.title}</span><span className="text-xs text-muted-foreground">{name(t.owner_id)}</span>
            </li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="Attendees and rating">
        <p className="text-sm">{meeting.attendee_ids.map(name).join(', ')}</p>
        <p className="mt-2 text-sm font-medium">
          {meeting.average_rating === null ? 'No rating' : `Rating ${meeting.average_rating.toFixed(1)}`}
        </p>
      </SectionCard>
      <SectionCard title="Time per section">
        <ul className="space-y-1 text-sm">
          {meeting.sections.map((s) => (
            <li key={s.section} className="flex justify-between">
              <span>{SECTION_LABEL[s.section]}</span>
              <span className="tabular-nums text-muted-foreground">
                {s.ended_at ? clockText((Date.parse(s.ended_at) - Date.parse(s.started_at)) / 1000) : '—'}
              </span>
            </li>
          ))}
        </ul>
      </SectionCard>
    </div>
  )
}
