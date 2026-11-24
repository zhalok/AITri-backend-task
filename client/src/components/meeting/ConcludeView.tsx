import { useAuth } from '@/auth/AuthProvider'
import { Empty, SectionCard } from '@/components/SectionCard'
import { Button } from '@/components/ui/button'
import { useMembers, useRateMeeting, useTodos } from '@/hooks/queries'
import { dueLabel } from '@/lib/format'
import type { MeetingState } from '@/lib/types'
import { cn } from '@/lib/utils'

/** Conclude: recap the To-Dos made in this meeting, and let attending Admins/Team Members rate it. */
export function ConcludeView({ teamId, meeting }: { teamId: string; meeting: MeetingState }) {
  const { user, canWrite } = useAuth()
  const todos = useTodos(teamId)
  const members = useMembers(teamId)
  const rate = useRateMeeting(teamId)
  const name = (id: string) => members.data?.find((u) => u.id === id)?.name ?? id
  const created = (todos.data ?? []).filter((t) => t.created_in_meeting_id === meeting.id)
  const mine = user ? meeting.ratings[user.id] : undefined
  const canRate = canWrite && meeting.status === 'active' && !!user && meeting.attendee_ids.includes(user.id)

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <SectionCard title="New To-Dos" description="Created during this meeting.">
        {created.length === 0 && <Empty>No To-Dos were created in this meeting.</Empty>}
        <ul className="divide-y text-sm">
          {created.map((t) => (
            <li key={t.id} className="flex items-center justify-between gap-3 py-2">
              <span>{t.title}</span>
              <span className="shrink-0 text-xs text-muted-foreground">{name(t.owner_id)} · due {dueLabel(t.due_date)}</span>
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard title="Rate this meeting" description="1 to 10. You can change your rating until the meeting ends.">
        {canRate ? (
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Your rating">
            {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
              <Button key={n} size="icon" variant={mine === n ? 'default' : 'outline'}
                      aria-pressed={mine === n} disabled={rate.isPending}
                      onClick={() => rate.mutate({ meetingId: meeting.id, rating: n })}>
                {n}
              </Button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Only attending Admins and Team Members rate.</p>
        )}
        <div className="mt-4 border-t pt-3 text-sm">
          <div className={cn('font-medium', meeting.average_rating === null && 'text-muted-foreground')}>
            {meeting.average_rating === null ? 'No ratings yet' : `Average ${meeting.average_rating.toFixed(1)}`}
          </div>
          <ul className="mt-1 space-y-0.5 text-muted-foreground">
            {Object.entries(meeting.ratings).map(([id, r]) => <li key={id}>{name(id)}: {r}</li>)}
          </ul>
        </div>
      </SectionCard>
    </div>
  )
}
