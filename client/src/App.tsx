import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/AuthProvider'
import AppShell from './components/AppShell'
import MeetingPage from './pages/MeetingPage'
import LoginPage from './pages/LoginPage'
import TeamPage from './pages/TeamPage'
import TeamRedirect from './pages/TeamRedirect'

export default function App() {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-10 text-sm text-muted-foreground">Loading…</div>
  if (!user) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    )
  }
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<TeamRedirect />} />
        <Route path="teams/:teamId" element={<TeamPage />} />
        <Route path="teams/:teamId/meeting" element={<MeetingPage />} />
        <Route path="teams/:teamId/meeting/:meetingId" element={<MeetingPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
