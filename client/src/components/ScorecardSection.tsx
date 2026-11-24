import { TriangleAlert } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { useAuth } from '@/auth/AuthProvider'
import { Empty, ErrorNote, LoadingRows, SectionCard } from '@/components/SectionCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useMakeItAnIssue, useMembers, useScorecard, useSetScore } from '@/hooks/queries'
import { fmtNum, goalText, num, STATUS_DOT, STATUS_LABEL, weekLabel } from '@/lib/format'
import type { MeasurableStatus } from '@/lib/types'

/** How long after the last change a score is saved by itself. Stepping with the arrows, or a pause in typing. */
const AUTOSAVE_MS = 400

function ScoreCell({
  value, status, editable, saving, onSave, onMakeIssue, label,
}: {
  value: string | null; status: MeasurableStatus; editable: boolean; saving: boolean
  /** Saves `n`, telling the server which stored value (`seen`) it is based on. Rejects if the cell had changed. */
  onSave: (n: number, seen: number | null) => Promise<unknown>; onMakeIssue: () => void; label: string
}) {
  const [draft, setDraft] = useState(fmtNum(value))
  const focused = useRef(false)
  const cancelled = useRef(false) // Escape: the blur that follows must not save
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const base = useRef<number | null>(num(value)) // the stored value our next save is based on
  const inFlight = useRef(false)
  const queued = useRef<number | null>(null) // an edit made while a save was running
  const resync = useRef(false) // a save was refused: show the stored value even if the box still has focus

  // Follow the stored value (a teammate's edit, or our own save coming back). Never overwrite what the user is
  // typing, except after a refused save: then the box must show what is really stored.
  useEffect(() => {
    base.current = num(value)
    if (!focused.current || resync.current) {
      setDraft(fmtNum(value))
      resync.current = false
    }
  }, [value])
  useEffect(() => () => clearTimeout(timer.current), [])

  /** One save at a time per cell, each based on the value the previous one left: two quick edits must not
   *  conflict with each other. A refused save drops anything queued behind it, since that was a stale view too. */
  async function send(n: number) {
    if (inFlight.current) {
      queued.current = n
      return
    }
    inFlight.current = true
    try {
      await onSave(n, base.current)
      base.current = n
    } catch {
      queued.current = null
      resync.current = true // the server said no (stale or otherwise); the refetch brings the stored value
    } finally {
      inFlight.current = false
    }
    if (queued.current !== null) {
      const next = queued.current
      queued.current = null
      if (next !== base.current) void send(next)
    }
  }

  /** Saves a valid number that differs from what is stored. False when the text is empty or not a number. */
  function save(text: string): boolean {
    const n = text.trim() === '' ? null : Number(text)
    if (n === null || !Number.isFinite(n)) return false
    if (n !== base.current) void send(n)
    return true
  }

  function change(text: string) {
    setDraft(text)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => save(text), AUTOSAVE_MS) // an empty or half-typed box just waits
  }

  function blur() {
    focused.current = false
    clearTimeout(timer.current)
    if (cancelled.current) {
      cancelled.current = false
      return setDraft(fmtNum(value))
    }
    if (!save(draft)) setDraft(fmtNum(value)) // can't clear a score; revert
  }

  const dot = (
    <span role="img" title={STATUS_LABEL[status]} aria-label={STATUS_LABEL[status]} data-status={status}
          className={`size-2 shrink-0 rounded-full ${STATUS_DOT[status]}`} />
  )
  if (!editable) {
    return (
      <span className="flex items-center justify-end gap-2 px-2 tabular-nums">{dot}{fmtNum(value) || '–'}</span>
    )
  }
  return (
    <div className="group flex items-center justify-end gap-1">
      {dot}
      {status === 'off_track' && <Button variant="ghost" size="icon-xs" title="Make it an Issue" aria-label={`Make it an Issue: ${label}`}
              className="opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
              onClick={onMakeIssue}>
        <TriangleAlert />
      </Button>}
      {/* Not disabled while saving: a disabled input drops focus, which would break stepping with the arrows. */}
      <Input
        type="number" step="any" inputMode="decimal" aria-label={`Score: ${label}`} value={draft}
        placeholder="–" aria-busy={saving}
        className={`h-7 w-20 px-2 text-right tabular-nums ${saving ? 'opacity-60' : ''}`}
        onFocus={() => { focused.current = true }}
        onChange={(e) => change(e.target.value)}
        onBlur={blur}
        onKeyDown={(e) => {
          if (e.key === 'Enter') e.currentTarget.blur()
          if (e.key === 'Escape') { cancelled.current = true; e.currentTarget.blur() }
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
    <SectionCard title="Scorecard" description="Weekly Measurables, last 13 weeks. Edit a score inline; use ⚠ on an off-track week to make it an Issue.">
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
              {scorecard.data.rows.map(({ measurable: m, scores, statuses }) => (
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
                        value={scores[w] ?? null}
                        status={statuses[w]}
                        editable={canWrite}
                        saving={setScore.isPending && setScore.variables?.measurableId === m.id && setScore.variables.week === w}
                        label={`${m.name}, week of ${weekLabel(w)}`}
                        onSave={(value, seen) => setScore.mutateAsync({ measurableId: m.id, week: w, value, seen })}
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
