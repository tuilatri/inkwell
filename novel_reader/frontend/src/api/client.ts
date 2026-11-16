export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function refreshSession(): Promise<boolean> {
  try {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    return response.ok
  } catch {
    return false
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}, retried = false): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('X-Requested-With', 'XMLHttpRequest')
  if (init.body instanceof FormData === false && init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(path, {
    ...init,
    headers,
    credentials: 'include',
  })
  if (response.status === 401 && !path.endsWith('/auth/login') && !path.endsWith('/auth/refresh')) {
    // Access token expired: rotate the refresh cookie once, then replay the call.
    if (!retried && (await refreshSession())) {
      return apiFetch<T>(path, init, true)
    }
    window.location.assign('/login')
    throw new ApiError(401, 'not authenticated')
  }
  if (!response.ok) {
    const detail = await response.text().catch(() => '')
    throw new ApiError(response.status, detail || response.statusText)
  }
  const contentType = response.headers.get('content-type') || ''
  return (contentType.includes('application/json') ? response.json() : response.text()) as Promise<T>
}
