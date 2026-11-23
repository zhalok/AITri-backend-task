import { useState, type FormEvent } from 'react'
import { OptionSelect } from '@/components/OptionSelect'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { useAuth } from '@/auth/AuthProvider'
import { useCreateTodo, useMembers, useSolveIssue } from '@/hooks/queries'
import type { Issue } from '@/lib/types'

export function SolveIssueDialog({ teamId, issue, onClose }: { teamId: string; issue: Issue | null; onClose: () => void }) {
  const solve = useSolveIssue(teamId)
  const [note, setNote] = useState('')

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!issue || !note.trim()) return
    solve.mutate({ issueId: issue.id, note: note.trim() }, { onSuccess: () => { setNote(''); onClose() } })
  }

  return (
    <Dialog open={issue !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Solve Issue</DialogTitle>
            <DialogDescription>{issue?.title}</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="solve-note">Resolution note (required)</Label>
            <Textarea id="solve-note" value={note} onChange={(e) => setNote(e.target.value)} rows={4} autoFocus
                      placeholder="What was decided?" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={!note.trim() || solve.isPending}>Solve</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function AddTodoDialog({ teamId, issue, onClose }: { teamId: string; issue: Issue | null; onClose: () => void }) {
  const { user } = useAuth()
  const members = useMembers(teamId)
  const create = useCreateTodo(teamId)
  const [title, setTitle] = useState('')
  const [ownerId, setOwnerId] = useState('')
  const owner = ownerId || user?.id || ''  // defaults to you, can be changed

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!issue || !title.trim() || !owner) return
    create.mutate({ issueId: issue.id, title: title.trim(), ownerId: owner }, {
      onSuccess: () => { setTitle(''); setOwnerId(''); onClose() },
    })
  }

  return (
    <Dialog open={issue !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <form onSubmit={submit} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Add a To-Do</DialogTitle>
            <DialogDescription>Follow-up for “{issue?.title}”. Due in 7 days.</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="todo-title">To-Do</Label>
            <Input id="todo-title" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus
                   placeholder="What needs to happen?" />
          </div>
          <div className="space-y-1.5">
            <Label>Owner</Label>
            <OptionSelect ariaLabel="Owner" className="w-full" value={owner} onChange={setOwnerId}
                          placeholder="Choose an owner"
                          options={(members.data ?? []).map((u) => ({ value: u.id, label: u.name }))} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={!title.trim() || !owner || create.isPending}>Add To-Do</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
