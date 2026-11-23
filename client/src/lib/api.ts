const TOKEN_KEY = 'l10_token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

export class ApiError extends Error {
  status: number
  code: string
  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

/** Fired when the server says the token is no longer valid, so the app can return to sign-in. */
export const UNAUTHORIZED_EVENT = 'l10:unauthorized'

export interface ApiResult<T> { data: T; status: number }

async function request<T>(method: string, path: string, body?: unknown): Promise<ApiResult<T>> {
  const token = tokenStore.get()
  const res = await fetch(`/api${path}`, {
    method,
    headers: {
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  const payload = await res.json().catch(() => null)
  if (!res.ok) {
    if (res.status === 401 && path !== '/auth/login') window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
    // Domain errors are {error, message}; request validation errors are {detail: [...]}.
    const message =
      payload?.message ??
      (Array.isArray(payload?.detail) ? payload.detail.map((d: { msg: string }) => d.msg).join('; ') : null) ??
      `Request failed (${res.status})`
    throw new ApiError(res.status, payload?.error ?? 'error', message)
  }
  return { data: payload as T, status: res.status }
}

export const api = {
  get: async <T>(path: string) => (await request<T>('GET', path)).data,
  post: async <T>(path: string, body?: unknown) => (await request<T>('POST', path, body)).data,
  put: async <T>(path: string, body?: unknown) => (await request<T>('PUT', path, body)).data,
  patch: async <T>(path: string, body?: unknown) => (await request<T>('PATCH', path, body)).data,
  delete: async <T>(path: string) => (await request<T>('DELETE', path)).data,
  /** Same as post, but keeps the status code (Make it an Issue is 201 created / 200 already existed). */
  postWithStatus: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
}
