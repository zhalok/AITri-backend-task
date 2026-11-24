import { Empty, ErrorNote, LoadingRows, SectionCard } from '@/components/SectionCard'
import { Badge } from '@/components/ui/badge'
import { useMeetingSummary } from '@/hooks/queries'
import { clockText, fmtNum, goalText, SECTION_LABEL, STATUS_DOT, STATUS_LABEL, weekLabel } from '@/lib/format'
import type { MeetingState } from '@/lib/types'

/** What the team sees after the facilitator ends the meeting. Everything comes from the summary endpoint. */
export function MeetingSummary({ teamId, meeting }: { teamId: string; meeting: MeetingState }) {
  const summary = useMeetingSummary(teamId, meeting.id, meeting.status === 'ended')
  const s = summary.data
  const name = (id: string) => s?.attendees.find((a) => a.id === id)?.name ?? id

  if (summary.isLoading) return <LoadingRows />
  if (summary.error) return <ErrorNote error={summary.error} />
  if (!s) return null

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <SectionCard title="Measurable statuses" description={`Last closed week, from ${weekLabel(s.week_start)}.`}>
        {s.measurables.length === 0 && <Empty>This team has no Measurables.</Empty>}
        <ul className="divide-y text-sm">
          {s.measurables.map((m) => (
            <li key={m.measurable_id} className="flex items-center gap-3 py-2" data-testid="summary-measurable">
              <span className={`size-2 shrink-0 rounded-full ${STATUS_DOT[m.status]}`} aria-hidden />
              <div className="min-w-0 flex-1">
                <div>{m.name}</div>
                <div className="text-xs text-muted-foreground">goal {goalText(m)} {m.unit}</div>
              </div>
              <span className="tabular-nums">{m.score === null ? 'no score' : fmtNum(m.score)}</span>
              <Badge variant={m.status === 'off_track' ? 'destructive' : m.status === 'on_track' ? 'default' : 'secondary'}>
                {STATUS_LABEL[m.status]}
              </Badge>
            </li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="Issues solved">
        {s.issues_solved.length === 0 && <Empty>No Issues were solved.</Empty>}
        <ul className="divide-y text-sm">
          {s.issues_solved.map((i) => (
            <li key={i.id} className="py-2">
              <div>{i.title}</div>
              <div className="text-xs text-muted-foreground">{name(i.owner_id)} · {i.resolution_note}</div>
            </li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="To-Dos created">
        {s.todos_created.length === 0 && <Empty>No To-Dos were created.</Empty>}
        <ul className="divide-y text-sm">
          {s.todos_created.map((t) => (
            <li key={t.id} className="flex justify-between gap-3 py-2">
              <span>{t.title}</span><span className="text-xs text-muted-foreground">{name(t.owner_id)}</span>
            </li>
          ))}
        </ul>
      </SectionCard>
      <SectionCard title="Attendees and rating">
        <p className="text-sm">{s.attendees.map((a) => a.name).join(', ')}</p>
        <p className="mt-2 text-sm font-medium" data-testid="summary-rating">
          {s.rating.average === null ? 'No ratings' : `Rating ${s.rating.average.toFixed(1)} from ${s.rating.count}`}
        </p>
        {s.rating.count > 0 && (
          <ul className="mt-1 text-xs text-muted-foreground">
            {Object.entries(s.rating.by_user).map(([id, r]) => <li key={id}>{name(id)}: {r}</li>)}
          </ul>
        )}
      </SectionCard>
      <SectionCard title="Time per section">
        <ul className="space-y-1 text-sm">
          {meeting.sections.map((sec) => (
            <li key={sec.section} className="flex justify-between">
              <span>{SECTION_LABEL[sec.section]}</span>
              <span className="tabular-nums text-muted-foreground">
                {sec.ended_at ? clockText((Date.parse(sec.ended_at) - Date.parse(sec.started_at)) / 1000) : '—'}
              </span>
            </li>
          ))}
        </ul>
      </SectionCard>
    </div>
  )
}
