import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useRef } from 'react'
import { key } from '@/hooks/queries'
import { tokenStore } from '@/lib/api'

/** What the server says changed -> which cached queries to refresh. Events never carry data. */
const KIND_TO_QUERY: Record<string, string> = { scorecard: 'scorecard', issues: 'issues', todos: 'todos', meeting: 'meeting' }

const NOT_ALLOWED = [4401, 4403] // not signed in / not your team: retrying cannot help

/**
 * One live socket for one team. On every (re)connect the server sends "ready" and we refetch the team's whole
 * cache, which is what makes refreshes, late joins and dropped connections safe.
 * `endpoint` picks the responsibility: "sync" is only the data feed; "meeting" is the data feed plus being
 * in the team's meeting (connecting joins it, closing it leaves it).
 */
function useLiveSocket(teamId: string, endpoint: 'sync' | 'meeting') {
  const qc = useQueryClient()
  const socketRef = useRef<WebSocket | null>(null)
  const stoppedRef = useRef(false)

  useEffect(() => {
    const token = tokenStore.get()
    if (!teamId || !token) return
    let socket: WebSocket | null = null
    let retry: ReturnType<typeof setTimeout> | undefined
    let attempt = 0
    let stopped = false
    stoppedRef.current = false

    const connect = () => {
      const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
      socket = new WebSocket(`${scheme}://${location.host}/api/ws/teams/${teamId}/${endpoint}`)
      socketRef.current = socket
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
        if (stopped || stoppedRef.current || NOT_ALLOWED.includes(e.code)) return
        retry = setTimeout(connect, Math.min(1000 * 2 ** attempt++, 15000))
      }
    }
    connect()

    return () => {
      stopped = true
      clearTimeout(retry)
      socket?.close()
    }
  }, [teamId, endpoint, qc])

  /** Close the socket and stop reconnecting. */
  const close = useCallback(() => {
    stoppedRef.current = true
    socketRef.current?.close()
  }, [])

  return { close }
}

/** The Team page's live feed. It never changes who is in a meeting. */
export function useTeamSocket(teamId: string) {
  useLiveSocket(teamId, 'sync')
}

/** The Meeting page's socket: the live feed, and this socket IS you being in the team's meeting. */
export function useMeetingSocket(teamId: string) {
  const { close } = useLiveSocket(teamId, 'meeting')
  /** Leave the meeting: the user's last meeting socket closing takes them off the attendee list. */
  return { leave: close }
}
