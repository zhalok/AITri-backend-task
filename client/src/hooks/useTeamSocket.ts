import { useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { key } from '@/hooks/queries'
import { tokenStore } from '@/lib/api'

/** What the server says changed -> which cached queries to refresh. Events never carry data. */
const KIND_TO_QUERY: Record<string, string> = { scorecard: 'scorecard', issues: 'issues', todos: 'todos', meeting: 'meeting' }

const NOT_ALLOWED = [4401, 4403] // not signed in / not your team: retrying cannot help

/**
 * Keeps one team's data live. Both the Team page and the Meeting page call this, so a change made on
 * either shows up on the other. On every (re)connect the server sends "ready" and we refetch the team's
 * whole cache, which is what makes refreshes, late joins and dropped connections safe.
 */
export function useTeamSocket(teamId: string) {
  const qc = useQueryClient()

  useEffect(() => {
    const token = tokenStore.get()
    if (!teamId || !token) return
    let socket: WebSocket | null = null
    let retry: ReturnType<typeof setTimeout> | undefined
    let attempt = 0
    let stopped = false

    const connect = () => {
      const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
      socket = new WebSocket(`${scheme}://${location.host}/api/ws/teams/${teamId}`)
      socket.onopen = () => socket?.send(JSON.stringify({ type: 'auth', token }))
      socket.onmessage = (e) => {
        const msg = JSON.parse(e.data) as { type: string; kind?: string }
        if (msg.type === 'ready') {
          attempt = 0
          qc.invalidateQueries({ queryKey: ['team', teamId] })
        } else if (msg.type === 'change' && msg.kind && KIND_TO_QUERY[msg.kind]) {
          qc.invalidateQueries({ queryKey: key(teamId, KIND_TO_QUERY[msg.kind]) })
        }
      }
      socket.onclose = (e) => {
        if (stopped || NOT_ALLOWED.includes(e.code)) return
        retry = setTimeout(connect, Math.min(1000 * 2 ** attempt++, 15000))
      }
    }
    connect()

    return () => {
      stopped = true
      clearTimeout(retry)
      socket?.close()
    }
  }, [teamId, qc])
}
