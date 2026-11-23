import { useState } from 'react'
import { useAuth } from '@/auth/AuthProvider'
import { Empty, ErrorNote, LoadingRows, SectionCard } from '@/components/SectionCard'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { useIssues, useMembers, useSetTodoDone, useTodos } from '@/hooks/queries'
import { dateTimeLabel, dueLabel } from '@/lib/format'
import { cn } from '@/lib/utils'

export default function TodosSection({ teamId }: { teamId: string }) {
  const { canWrite } = useAuth()
  const todos = useTodos(teamId)
  const members = useMembers(teamId)
  const unsolved = useIssues(teamId, 'unsolved')
  const solved = useIssues(teamId, 'solved')
  const setDone = useSetTodoDone(teamId)
  const [hideDone, setHideDone] = useState(false)

  const owner = (id: string) => members.data?.find((u) => u.id === id)?.name ?? id
  const issueTitle = (id: string | null) =>
    id ? [...(unsolved.data ?? []), ...(solved.data ?? [])].find((i) => i.id === id)?.title ?? null : null
  const visible = (todos.data ?? []).filter((t) => !(hideDone && t.done_at))

  return (
    <SectionCard
      title="To-Dos"
      description="Due dates are calendar days in company time. Overdue means not done and due before today."
      actions={
        <div className="flex items-center gap-2">
          <Checkbox id="hide-done" checked={hideDone} onCheckedChange={(c) => setHideDone(c === true)} />
          <Label htmlFor="hide-done" className="text-xs font-normal">Hide completed</Label>
        </div>
      }
    >
      {todos.isLoading && <LoadingRows />}
      {todos.error && <ErrorNote error={todos.error} />}
      {todos.data && visible.length === 0 && <Empty>{hideDone ? 'No open To-Dos.' : 'No To-Dos yet.'}</Empty>}
      <ul className="divide-y">
        {visible.map((t) => (
          <li key={t.id} className="flex items-start gap-3 py-2.5">
            <Checkbox
              aria-label={`Mark done: ${t.title}`} className="mt-0.5" checked={t.done_at !== null}
              disabled={!canWrite || setDone.isPending}
              onCheckedChange={(checked) => setDone.mutate({ todoId: t.id, done: checked === true })}
            />
            <div className="min-w-0 flex-1">
              <div className={cn('font-medium', t.done_at && 'text-muted-foreground line-through')}>{t.title}</div>
              <div className="text-xs text-muted-foreground">
                {owner(t.owner_id)} · due {dueLabel(t.due_date)}
                {t.done_at && ` · done ${dateTimeLabel(t.done_at)}`}
                {issueTitle(t.source_issue_id) && ` · from “${issueTitle(t.source_issue_id)}”`}
              </div>
            </div>
            {t.is_overdue && <Badge variant="destructive">Overdue</Badge>}
          </li>
        ))}
      </ul>
    </SectionCard>
  )
}
