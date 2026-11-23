import { Navigate } from 'react-router-dom'
import { Empty, ErrorNote, LoadingRows } from '@/components/SectionCard'
import { useTeams } from '@/hooks/queries'

/** "/" sends you to the team you used last, or your first team. */
export default function TeamRedirect() {
  const teams = useTeams()
  if (teams.isLoading) return <LoadingRows />
  if (teams.error) return <ErrorNote error={teams.error} />
  const list = teams.data ?? []
  if (list.length === 0) return <Empty>You are not on any team yet.</Empty>
  const last = localStorage.getItem('l10_last_team')
  const target = list.find((t) => t.id === last) ?? list[0]
  return <Navigate to={`/teams/${target.id}`} replace />
}
