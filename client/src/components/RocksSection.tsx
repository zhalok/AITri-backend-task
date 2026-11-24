import { CircleCheck, Circle, ChevronRight } from 'lucide-react'
import { Empty, ErrorNote, LoadingRows, SectionCard } from '@/components/SectionCard'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { useMembers, useRocks } from '@/hooks/queries'
import { dueLabel, roleLabel } from '@/lib/format'

export default function RocksSection({ teamId }: { teamId: string }) {
  const rocks = useRocks(teamId)
  const members = useMembers(teamId)
  const owner = (id: string) => members.data?.find((u) => u.id === id)?.name ?? id

  return (
    <SectionCard title="Rocks" description="This quarter's goals. Read-only. Expand a Rock to see its Milestones.">
      {rocks.isLoading && <LoadingRows />}
      {rocks.error && <ErrorNote error={rocks.error} />}
      {rocks.data?.length === 0 && <Empty>No Rocks this quarter.</Empty>}
      <div className="divide-y">
        {rocks.data?.map((r) => {
          const done = r.milestones.filter((m) => m.done).length
          return (
            <Collapsible key={r.id} className="py-2">
              <CollapsibleTrigger className="group flex w-full items-center gap-3 rounded-md px-1 py-1 text-left hover:bg-muted/50">
                <ChevronRight className="size-4 shrink-0 transition-transform group-data-[panel-open]:rotate-90" />
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{r.title}</div>
                  <div className="text-xs text-muted-foreground">{owner(r.owner_id)} · {r.quarter}</div>
                </div>
                <span className="text-xs text-muted-foreground tabular-nums">
                  <span className="font-medium text-foreground">{r.progress}%</span>
                  {' · '}{r.milestones.length ? `${done} of ${r.milestones.length} milestones` : 'No milestones'}
                </span>
                <Badge variant={r.status === 'complete' ? 'default' : r.status === 'off_track' ? 'destructive' : 'secondary'}
                       className="capitalize">{roleLabel(r.status)}</Badge>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <ul className="ml-8 mt-1 space-y-1.5 pb-1">
                  {r.milestones.length === 0 && <li className="text-sm text-muted-foreground">No milestones.</li>}
                  {r.milestones.map((m) => (
                    <li key={m.id} className="flex items-center gap-2 text-sm">
                      {m.done ? <CircleCheck className="size-4 text-primary" /> : <Circle className="size-4 text-muted-foreground" />}
                      <span className={m.done ? 'text-muted-foreground line-through' : ''}>{m.title}</span>
                      <span className="ml-auto text-xs text-muted-foreground">due {dueLabel(m.due_date)}</span>
                    </li>
                  ))}
                </ul>
              </CollapsibleContent>
            </Collapsible>
          )
        })}
      </div>
    </SectionCard>
  )
}
