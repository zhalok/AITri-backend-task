import { Check } from 'lucide-react'
import { SectionCard } from '@/components/SectionCard'
import { Badge } from '@/components/ui/badge'
import { clockText, SECTION_LABEL, SECTION_MINUTES, SECTION_ORDER } from '@/lib/format'
import type { MeetingState } from '@/lib/types'
import { cn } from '@/lib/utils'
import { useSectionClock } from './useSectionClock'

export function AgendaTimer({ meeting, receivedAt }: { meeting: MeetingState; receivedAt: number }) {
  const clock = useSectionClock(meeting, receivedAt)
  const currentIdx = SECTION_ORDER.indexOf(meeting.current_section)
  const ended = !!meeting.ended_at

  return (
    <SectionCard title="Agenda">
      <ol className="space-y-1.5">
        {SECTION_ORDER.map((s, i) => {
          const done = ended || i < currentIdx
          const current = !ended && i === currentIdx
          return (
            <li key={s} className={cn('flex items-center gap-2 rounded-md px-2 py-1.5 text-sm',
              current && 'bg-primary/10 font-medium text-primary', done && 'text-muted-foreground')}>
              <span className="grid size-5 place-items-center rounded-full border text-[11px]">
                {done ? <Check className="size-3" /> : i + 1}
              </span>
              <span>{SECTION_LABEL[s]}</span>
              <span className="ml-auto text-xs">{SECTION_MINUTES[s]} min</span>
            </li>
          )
        })}
      </ol>

      {clock && !ended && (
        <div className="mt-4 rounded-lg border p-3 text-center" aria-live="off">
          <div className="text-xs text-muted-foreground">{SECTION_LABEL[meeting.current_section]} timer</div>
          {clock.overTime ? (
            <>
              <div className="text-3xl font-semibold tabular-nums text-destructive">+{clockText(clock.overBy)}</div>
              <Badge variant="destructive">Over time</Badge>
            </>
          ) : (
            <div className="text-3xl font-semibold tabular-nums">{clockText(clock.limit - clock.elapsed)}</div>
          )}
          <div className="mt-1 text-xs text-muted-foreground">
            {clockText(clock.elapsed)} of {clockText(clock.limit)} elapsed
          </div>
        </div>
      )}
    </SectionCard>
  )
}
