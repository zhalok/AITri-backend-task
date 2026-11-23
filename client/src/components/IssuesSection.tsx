import { CheckCheck, ListPlus } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useAuth } from '@/auth/AuthProvider'
import { AddTodoDialog, SolveIssueDialog } from '@/components/IssueDialogs'
import { OptionSelect, type Option } from '@/components/OptionSelect'
import { Empty, ErrorNote, LoadingRows, SectionCard } from '@/components/SectionCard'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useCreateIssue, useIssues, useMembers, useScorecard, useSetPriority } from '@/hooks/queries'
import { dateTimeLabel, weekLabel } from '@/lib/format'
import type { Issue } from '@/lib/types'

const PRIORITIES: Option[] = [
  { value: 'none', label: 'None' },
  ...[5, 4, 3, 2, 1].map((p) => ({ value: String(p), label: `P${p}` })),
]
const toPriority = (v: string) => (v === 'none' ? null : Number(v))

function CreateIssueForm({ teamId }: { teamId: string }) {
  const create = useCreateIssue(teamId)
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState('none')

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    create.mutate({ title: title.trim(), priority: toPriority(priority) }, {
      onSuccess: () => { setTitle(''); setPriority('none') },
    })
  }

  return (
    <form onSubmit={submit} className="mb-3 flex gap-2">
      <Input aria-label="New Issue title" placeholder="Add an Issue…" value={title} onChange={(e) => setTitle(e.target.value)} />
      <OptionSelect ariaLabel="Priority" className="w-24" value={priority} onChange={setPriority} options={PRIORITIES} />
      <Button type="submit" disabled={!title.trim() || create.isPending}>Add</Button>
    </form>
  )
}

export default function IssuesSection({ teamId }: { teamId: string }) {
  const { canWrite } = useAuth()
  const unsolved = useIssues(teamId, 'unsolved')
  const solved = useIssues(teamId, 'solved')
  const members = useMembers(teamId)
  const scorecard = useScorecard(teamId)
  const setPriority = useSetPriority(teamId)
  const [solving, setSolving] = useState<Issue | null>(null)
  const [addingTodo, setAddingTodo] = useState<Issue | null>(null)

  const owner = (id: string) => members.data?.find((u) => u.id === id)?.name ?? id
  const source = (i: Issue) => {
    if (!i.source_measurable_id || !i.source_week_start) return null
    const name = scorecard.data?.rows.find((r) => r.measurable.id === i.source_measurable_id)?.measurable.name
    return `${name ?? 'Measurable'} · week of ${weekLabel(i.source_week_start)}`
  }

  return (
    <SectionCard title="Issues" description="Worked top to bottom: priority 5 first, oldest first within a priority.">
      {canWrite && <CreateIssueForm teamId={teamId} />}
      <Tabs defaultValue="unsolved">
        <TabsList>
          <TabsTrigger value="unsolved">Unsolved{unsolved.data ? ` (${unsolved.data.length})` : ''}</TabsTrigger>
          <TabsTrigger value="solved">Solved{solved.data ? ` (${solved.data.length})` : ''}</TabsTrigger>
        </TabsList>

        <TabsContent value="unsolved">
          {unsolved.isLoading && <LoadingRows />}
          {unsolved.error && <ErrorNote error={unsolved.error} />}
          {unsolved.data?.length === 0 && <Empty>No unsolved Issues. Nice.</Empty>}
          {!!unsolved.data?.length && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24">Priority</TableHead>
                  <TableHead>Issue</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Created</TableHead>
                  {canWrite && <TableHead className="w-28" />}
                </TableRow>
              </TableHeader>
              <TableBody>
                {unsolved.data.map((i) => (
                  <TableRow key={i.id}>
                    <TableCell>
                      {canWrite ? (
                        <OptionSelect ariaLabel={`Priority: ${i.title}`} className="h-7 w-20" options={PRIORITIES}
                                      value={i.priority === null ? 'none' : String(i.priority)}
                                      onChange={(v) => setPriority.mutate({ issueId: i.id, priority: toPriority(v) })} />
                      ) : (
                        <Badge variant="secondary">{i.priority === null ? '–' : `P${i.priority}`}</Badge>
                      )}
                    </TableCell>
                    <TableCell className="whitespace-normal">
                      <div className="font-medium">{i.title}</div>
                      {source(i) && <div className="text-xs text-muted-foreground">From {source(i)}</div>}
                    </TableCell>
                    <TableCell>{owner(i.owner_id)}</TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">{dateTimeLabel(i.created_at)}</TableCell>
                    {canWrite && (
                      <TableCell>
                        <div className="flex justify-end gap-1">
                          <Button variant="outline" size="icon-sm" title="Add a To-Do" aria-label={`Add a To-Do for ${i.title}`}
                                  onClick={() => setAddingTodo(i)}><ListPlus /></Button>
                          <Button variant="outline" size="icon-sm" title="Solve" aria-label={`Solve ${i.title}`}
                                  onClick={() => setSolving(i)}><CheckCheck /></Button>
                        </div>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </TabsContent>

        <TabsContent value="solved">
          {solved.isLoading && <LoadingRows />}
          {solved.error && <ErrorNote error={solved.error} />}
          {solved.data?.length === 0 && <Empty>Nothing solved yet.</Empty>}
          {!!solved.data?.length && (
            <ul className="divide-y">
              {solved.data.map((i) => (
                <li key={i.id} className="space-y-0.5 py-2.5">
                  <div className="font-medium">{i.title}</div>
                  <div className="text-sm text-muted-foreground">{i.resolution_note}</div>
                  <div className="text-xs text-muted-foreground">
                    {owner(i.owner_id)} · solved {i.solved_at && dateTimeLabel(i.solved_at)}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </TabsContent>
      </Tabs>

      <SolveIssueDialog teamId={teamId} issue={solving} onClose={() => setSolving(null)} />
      <AddTodoDialog teamId={teamId} issue={addingTodo} onClose={() => setAddingTodo(null)} />
    </SectionCard>
  )
}
