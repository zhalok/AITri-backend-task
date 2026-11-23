// Mirrors the FastAPI response schemas. Decimals arrive as strings ("12.5000"), so convert with num().
export type Role = 'admin' | 'team_member' | 'observer'

export interface User { id: string; name: string; email: string; role: Role }
export interface Team { id: string; name: string }
export interface LoginResponse { access_token: string; token_type: string; expires_in: number; user: User }

export type GoalType = 'at_least' | 'at_most' | 'between' | 'exactly'
export interface Measurable {
  id: string; team_id: string; owner_id: string; name: string; unit: string
  goal_type: GoalType; goal_value: string | null; goal_min: string | null; goal_max: string | null
}
export interface ScorecardRow { measurable: Measurable; scores: Record<string, string | null> }
export interface Scorecard { weeks: string[]; rows: ScorecardRow[] }

export interface Issue {
  id: string; team_id: string; owner_id: string; title: string; priority: number | null
  created_at: string; solved_at: string | null; resolution_note: string | null
  source_measurable_id: string | null; source_week_start: string | null; solved_in_meeting_id: string | null
}

export interface Todo {
  id: string; team_id: string; owner_id: string; title: string; due_date: string
  done_at: string | null; created_at: string; source_issue_id: string | null
  created_in_meeting_id: string | null; is_overdue: boolean
}

export interface Milestone { id: string; rock_id: string; title: string; due_date: string; done: boolean }
export interface Rock {
  id: string; team_id: string; owner_id: string; title: string; quarter: string; status: string
  milestones: Milestone[]
}
