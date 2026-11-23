/** All server state lives here: one query hook per read, one mutation hook per write. */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/auth/AuthProvider'
import { api } from '@/lib/api'
import type { Issue, Rock, Scorecard, Team, Todo, User } from '@/lib/types'

const key = (teamId: string, part: string, ...rest: unknown[]) => ['team', teamId, part, ...rest]

export function useTeams() {
  const { scope } = useAuth()
  // Default routes are narrow (own teams); Admins ask for the wide one explicitly.
  return useQuery({ queryKey: ['teams', scope], queryFn: () => api.get<Team[]>(scope ? '/teams/all' : '/teams') })
}

export function useMembers(teamId: string) {
  const { scope } = useAuth()
  return useQuery({ queryKey: key(teamId, 'members'), queryFn: () => api.get<User[]>(`${scope}/teams/${teamId}/members`) })
}

export function useScorecard(teamId: string) {
  const { scope } = useAuth()
  return useQuery({ queryKey: key(teamId, 'scorecard'), queryFn: () => api.get<Scorecard>(`${scope}/teams/${teamId}/scorecard`) })
}

export function useIssues(teamId: string, status: 'unsolved' | 'solved') {
  const { scope } = useAuth()
  return useQuery({
    queryKey: key(teamId, 'issues', status),
    queryFn: () => api.get<Issue[]>(`${scope}/teams/${teamId}/issues?status=${status}`),
  })
}

export function useTodos(teamId: string) {
  const { scope } = useAuth()
  return useQuery({ queryKey: key(teamId, 'todos'), queryFn: () => api.get<Todo[]>(`${scope}/teams/${teamId}/todos`) })
}

export function useRocks(teamId: string) {
  const { scope } = useAuth()
  return useQuery({ queryKey: key(teamId, 'rocks'), queryFn: () => api.get<Rock[]>(`${scope}/teams/${teamId}/rocks`) })
}

// ---- writes: every one refreshes exactly what it can change ---------------------------------------

export function useSetScore(teamId: string) {
  const { scope } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { measurableId: string; week: string; value: number }) =>
      api.put(`${scope}/measurables/${v.measurableId}/scores/${v.week}`, { value: v.value }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key(teamId, 'scorecard') }),
  })
}

export function useMakeItAnIssue(teamId: string) {
  const { scope } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { measurableId: string; week: string }) =>
      api.postWithStatus<Issue>(`${scope}/measurables/${v.measurableId}/scores/${v.week}/issue`),
    onSuccess: () => qc.invalidateQueries({ queryKey: key(teamId, 'issues') }),
  })
}

export function useCreateIssue(teamId: string) {
  const { scope } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { title: string; priority: number | null }) =>
      api.post<Issue>(`${scope}/teams/${teamId}/issues`, v),
    onSuccess: () => qc.invalidateQueries({ queryKey: key(teamId, 'issues') }),
  })
}

export function useSetPriority(teamId: string) {
  const { scope } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { issueId: string; priority: number | null }) =>
      api.patch<Issue>(`${scope}/issues/${v.issueId}/priority`, { priority: v.priority }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key(teamId, 'issues') }),
  })
}

export function useSolveIssue(teamId: string) {
  const { scope } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { issueId: string; note: string }) =>
      api.post<Issue>(`${scope}/issues/${v.issueId}/solve`, { note: v.note }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key(teamId, 'issues') }),
  })
}

export function useCreateTodo(teamId: string) {
  const { scope } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { issueId: string; title: string; ownerId: string }) =>
      api.post<Todo>(`${scope}/issues/${v.issueId}/todos`, { title: v.title, owner_id: v.ownerId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: key(teamId, 'todos') }),
  })
}

export function useSetTodoDone(teamId: string) {
  const { scope } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { todoId: string; done: boolean }) =>
      v.done ? api.post<Todo>(`${scope}/todos/${v.todoId}/done`) : api.delete<Todo>(`${scope}/todos/${v.todoId}/done`),
    onSuccess: () => qc.invalidateQueries({ queryKey: key(teamId, 'todos') }),
  })
}
