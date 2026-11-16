import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiFetch } from './client'

describe('apiFetch', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('sends the session cookie and CSRF marker on every call', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await apiFetch<{ ok: boolean }>('/api/novels')

    expect(result).toEqual({ ok: true })
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.credentials).toBe('include')
    const headers = init.headers as Headers
    expect(headers.get('X-Requested-With')).toBe('XMLHttpRequest')
  })

  it('throws with the status on a failed request', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('nope', { status: 400 })))
    await expect(apiFetch('/api/search?q=x')).rejects.toMatchObject({ status: 400 })
  })

  it('refreshes the session once and retries after a 401', async () => {
    const ok = () => new Response(JSON.stringify({ ok: true }), {
      status: 200, headers: { 'content-type': 'application/json' },
    })
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response('expired', { status: 401 }))
      .mockResolvedValueOnce(new Response('{}', { status: 200 })) // /auth/refresh
      .mockResolvedValueOnce(ok())
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiFetch('/api/novels')).resolves.toEqual({ ok: true })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(fetchMock.mock.calls[1][0]).toBe('/api/auth/refresh')
    expect((fetchMock.mock.calls[1][1] as RequestInit).method).toBe('POST')
  })
})
