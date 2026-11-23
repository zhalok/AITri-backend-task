import { TriangleAlert } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { useAuth } from '@/auth/AuthProvider'
import { Empty, ErrorNote, LoadingRows, SectionCard } from '@/components/SectionCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useMakeItAnIssue, useMembers, useScorecard, useSetScore } from '@/hooks/queries'
import { fmtNum, goalText, num, weekLabel } from '@/lib/format'

function ScoreCell({
  value, editable, saving, onSave, onMakeIssue, label,
}: {
  value: string | null; editable: boolean; saving: boolean
  onSave: (n: number) => void; onMakeIssue: () => void; label: string
}) {
  const [draft, setDraft] = useState(fmtNum(value)) // resets when the cell is re-keyed after a save

  function commit() {
    const n = draft.trim() === '' ? null : Number(draft)
    if (n === null || !Number.isFinite(n)) return setDraft(fmtNum(value)) // can't clear a score; revert
    if (n !== num(value)) onSave(n)
  }

  if (!editable) return <span className="block px-2 text-right tabular-nums">{fmtNum(value) || '–'}</span>
  return (
    <div className="group flex items-center justify-end gap-1">
      <Button variant="ghost" size="icon-xs" title="Make it an Issue" aria-label={`Make it an Issue: ${label}`}
              className="opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
              onClick={onMakeIssue}>
        <TriangleAlert />
      </Button>
      <Input
        type="number" step="any" inputMode="decimal" aria-label={`Score: ${label}`} value={draft}
        placeholder="–" disabled={saving}
        className="h-7 w-20 px-2 text-right tabular-nums"
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') e.currentTarget.blur()
          if (e.key === 'Escape') { setDraft(fmtNum(value)); e.currentTarget.blur() }
        }}
      />
    </div>
  )
}

export default function ScorecardSection({ teamId }: { teamId: string }) {
  const { canWrite } = useAuth()
  const scorecard = useScorecard(teamId)
  const members = useMembers(teamId)
  const setScore = useSetScore(teamId)
  const makeIssue = useMakeItAnIssue(teamId)
  const owner = (id: string) => members.data?.find((u) => u.id === id)?.name ?? id

  function onMakeIssue(measurableId: string, week: string) {
    makeIssue.mutate({ measurableId, week }, {
      onSuccess: ({ data, status }) =>
        status === 201
          ? toast.success('Issue created', { description: data.title })
          : toast.info('An unsolved Issue already exists for this week', { description: data.title }),
    })
  }

  // Newest week first, so the current week is visible without scrolling.
  const weeks = [...(scorecard.data?.weeks ?? [])].reverse()
  const current = weeks[0]
  const lastClosed = weeks[1]

  return (
    <SectionCard title="Scorecard" description="Weekly Measurables, last 13 weeks. Edit a score inline; use ⚠ to make a week an Issue.">
      {scorecard.isLoading && <LoadingRows />}
      {scorecard.error && <ErrorNote error={scorecard.error} />}
      {scorecard.data && scorecard.data.rows.length === 0 && <Empty>This team has no Measurables yet.</Empty>}
      {scorecard.data && scorecard.data.rows.length > 0 && (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="sticky left-0 z-[1] min-w-56 bg-card">Measurable</TableHead>
                {weeks.map((w) => (
                  <TableHead key={w} className="min-w-28 text-right">
                    <div>{weekLabel(w)}</div>
                    {w === current && <div className="text-[10px] font-normal text-primary">current</div>}
                    {w === lastClosed && <div className="text-[10px] font-normal text-muted-foreground">last closed</div>}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {scorecard.data.rows.map(({ measurable: m, scores }) => (
                <TableRow key={m.id}>
                  <TableCell className="sticky left-0 z-[1] bg-card">
                    <div className="font-medium">{m.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {owner(m.owner_id)} · goal {goalText(m)} {m.unit}
                    </div>
                  </TableCell>
                  {weeks.map((w) => (
                    <TableCell key={w} className="text-right">
                      <ScoreCell
                        key={`${w}:${scores[w] ?? ''}`}
                        value={scores[w] ?? null}
                        editable={canWrite}
                        saving={setScore.isPending && setScore.variables?.measurableId === m.id && setScore.variables.week === w}
                        label={`${m.name}, week of ${weekLabel(w)}`}
                        onSave={(value) => setScore.mutate({ measurableId: m.id, week: w, value })}
                        onMakeIssue={() => onMakeIssue(m.id, w)}
                      />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </SectionCard>
  )
}
