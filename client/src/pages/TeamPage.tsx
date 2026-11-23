import { ShieldAlert } from 'lucide-react'
import { useParams } from 'react-router-dom'
import IssuesSection from '@/components/IssuesSection'
import RocksSection from '@/components/RocksSection'
import ScorecardSection from '@/components/ScorecardSection'
import TodosSection from '@/components/TodosSection'
import { useScorecard, useTeams } from '@/hooks/queries'
import { ApiError } from '@/lib/api'

export default function TeamPage() {
  const { teamId = '' } = useParams()
  const teams = useTeams()
  const scorecard = useScorecard(teamId)
  const team = teams.data?.find((t) => t.id === teamId)

  // A team you cannot see (even by a guessed id) is refused by the server; say so plainly.
  if (scorecard.error instanceof ApiError && [403, 404].includes(scorecard.error.status)) {
    return (
      <div className="flex flex-col items-center gap-2 py-24 text-center">
        <ShieldAlert className="size-8 text-muted-foreground" />
        <h1 className="text-lg font-semibold">You don't have access to this team</h1>
        <p className="text-sm text-muted-foreground">{scorecard.error.message}</p>
      </div>
    )
  }

  return (
    <>
      <h1 className="text-xl font-semibold tracking-tight">{team?.name ?? 'Team'}</h1>
      <ScorecardSection teamId={teamId} />
      <div className="grid gap-4 lg:grid-cols-2">
        <IssuesSection teamId={teamId} />
        <TodosSection teamId={teamId} />
      </div>
      <RocksSection teamId={teamId} />
    </>
  )
}
