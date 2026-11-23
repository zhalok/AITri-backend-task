import { useState, type FormEvent } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/auth/AuthProvider'

// Demo shortcuts for the seeded users (the seed has no passwords, so sign-in is by email).
const DEMO_USERS = [
  { email: 'avery@acme.test', label: 'Avery', role: 'Admin' },
  { email: 'blake@acme.test', label: 'Blake', role: 'Team Member' },
  { email: 'ellis@acme.test', label: 'Ellis', role: 'Observer' },
]

export default function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function signIn(address: string) {
    setBusy(true)
    setError(null)
    try {
      await login(address)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not sign in')
      setBusy(false)
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (email.trim()) void signIn(email.trim())
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Level 10</CardTitle>
          <CardDescription>Sign in with a seeded user's email.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={onSubmit} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" autoComplete="email" placeholder="avery@acme.test" value={email}
                     onChange={(e) => setEmail(e.target.value)} autoFocus />
            </div>
            {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={busy || !email.trim()}>Sign in</Button>
          </form>
          <div className="space-y-2 border-t pt-4">
            <p className="text-xs text-muted-foreground">Quick sign-in</p>
            <div className="flex flex-wrap gap-2">
              {DEMO_USERS.map((u) => (
                <Button key={u.email} variant="outline" size="sm" disabled={busy} onClick={() => void signIn(u.email)}>
                  {u.label} · {u.role}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
