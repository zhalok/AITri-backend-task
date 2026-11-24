import { useEffect, useState } from 'react'
import type { MeetingState } from '@/lib/types'

/**
 * The section timer is only a display. The server says how long the section has run as of the moment it
 * answered; between answers we add the time that has passed here. Every new state (an event, a refresh, a
 * reconnect) replaces the base value, so drift never builds up. An ended meeting stops ticking.
 */
export function useSectionClock(meeting: MeetingState | undefined, receivedAt: number) {
  const [now, setNow] = useState(() => Date.now())
  const running = !!meeting && meeting.status === 'active'

  useEffect(() => {
    if (!running) return
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [running])

  if (!meeting) return null
  const elapsed = meeting.section_elapsed_seconds + (running ? Math.max(0, (now - receivedAt) / 1000) : 0)
  const limit = meeting.section_duration_seconds
  return { elapsed, limit, overTime: elapsed > limit, overBy: elapsed - limit }
}
