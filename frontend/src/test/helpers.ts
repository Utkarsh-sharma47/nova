import type { ApiErrorBody } from '../api/types'

export function jsonResponse(
  body: unknown,
  init: ResponseInit = { status: 200 },
): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers ?? {}),
    },
  })
}

export function errorResponse(
  status: number,
  error: ApiErrorBody['error'],
): Response {
  return jsonResponse({ error }, { status })
}

export function mockFetch(handler: (url: string, init?: RequestInit) => Response | Promise<Response>) {
  return vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url =
      typeof input === 'string'
        ? input
        : input instanceof URL
          ? input.href
          : input.url
    return Promise.resolve(handler(url, init))
  })
}
