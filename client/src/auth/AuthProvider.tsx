import { useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, tokenStore, UNAUTHORIZED_EVENT } from '@/lib/api'
import type { LoginResponse, User } from '@/lib/types'

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string) => Promise<void>
  logout: () => void
  /** Observers are read-only. The server enforces this; the UI just doesn't offer what would be refused. */
  canWrite: boolean
  /** Admins reach every team through the /admin endpoints; everyone else uses the member endpoints. */
  scope: '' | '/admin'
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => tokenStore.get() !== null)

  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    if (!tokenStore.get()) return
    api.get<User>('/auth/me').then(setUser).catch(() => tokenStore.clear()).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, logout)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, logout)
  }, [logout])

  const login = useCallback(async (email: string) => {
    const res = await api.post<LoginResponse>('/auth/login', { email })
    tokenStore.set(res.access_token)
    queryClient.clear()
    setUser(res.user)
  }, [queryClient])

  const value = useMemo<AuthState>(
    () => ({
      user, loading, login, logout,
      canWrite: user !== null && user.role !== 'observer',
      scope: user?.role === 'admin' ? '/admin' : '',
    }),
    [user, loading, login, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
