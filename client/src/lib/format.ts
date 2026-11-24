import type { Measurable } from './types'

const COMPANY_TZ = 'America/Chicago'

/** "2026-11-09" -> a local Date at midnight, with no timezone shift (these are calendar dates). */
function calendarDate(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export const weekLabel = (iso: string) =>
  calendarDate(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })

export const dueLabel = (iso: string) =>
  calendarDate(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

/** Timestamps are UTC from the API; show them in company time. */
export const dateTimeLabel = (iso: string) =>
  new Date(iso).toLocaleString('en-US', {
    timeZone: COMPANY_TZ, month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  })

export function num(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

export const fmtNum = (value: string | number | null | undefined) => {
  const n = num(value)
  return n === null ? '' : String(Math.round(n * 10000) / 10000)
}

export function goalText(m: Pick<Measurable, 'goal_type' | 'goal_value' | 'goal_min' | 'goal_max'>): string {
  const v = fmtNum(m.goal_value)
  switch (m.goal_type) {
    case 'at_least': return `≥ ${v}`
    case 'at_most': return `≤ ${v}`
    case 'exactly': return `= ${v}`
    case 'between': return `${fmtNum(m.goal_min)} – ${fmtNum(m.goal_max)}`
  }
}

export const STATUS_LABEL = { on_track: 'On track', off_track: 'Off track', pending: 'Pending' } as const
export const STATUS_DOT = { on_track: 'bg-emerald-500', off_track: 'bg-red-500', pending: 'bg-amber-400' } as const

export const roleLabel = (role: string) => role.replace('_', ' ')

/** 75 -> "1:15". Whole seconds, minutes unpadded, as on a stopwatch. */
export function clockText(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

export const SECTION_LABEL = { scorecard: 'Scorecard', ids: 'IDS', conclude: 'Conclude' } as const
export const SECTION_MINUTES = { scorecard: 5, ids: 60, conclude: 10 } as const
export const SECTION_ORDER = ['scorecard', 'ids', 'conclude'] as const
