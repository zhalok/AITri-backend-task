import { LogOut } from 'lucide-react'
import { Outlet, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@/auth/AuthProvider'
import { OptionSelect } from '@/components/OptionSelect'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useTeams } from '@/hooks/queries'
import { roleLabel } from '@/lib/format'

export default function AppShell() {
  const { user, logout } = useAuth()
  const { teamId } = useParams()
  const navigate = useNavigate()
  const teams = useTeams()

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="sticky top-0 z-10 border-b bg-background">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-2.5">
          <span className="text-sm font-semibold tracking-tight">Level 10</span>
          <OptionSelect
            ariaLabel="Team"
            className="w-52"
            value={teams.data?.some((t) => t.id === teamId) ? teamId! : ''}
            placeholder={teams.isLoading ? 'Loading teams…' : 'Select a team'}
            options={(teams.data ?? []).map((t) => ({ value: t.id, label: t.name }))}
            onChange={(id) => {
              localStorage.setItem('l10_last_team', id)
              navigate(`/teams/${id}`)
            }}
          />
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span>{user?.name}</span>
            <Badge variant="secondary" className="capitalize">{roleLabel(user?.role ?? '')}</Badge>
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut /> Sign out
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl space-y-4 p-4">
        <Outlet />
      </main>
    </div>
  )
}
