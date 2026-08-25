import type { ApiErrorBody } from './types'

const DEFAULT_BASE_URL = 'http://localhost:8000'
const DEFAULT_TIMEOUT_MS = 30_000

export class ApiClientError extends Error {
  readonly code: string
  readonly status: number
  readonly details?: Record<string, unknown>
  readonly traceId?: string
  readonly retryable: boolean

  constructor(
    message: string,
    options: {
      code: string
      status: number
      details?: Record<string, unknown>
      traceId?: string
      retryable: boolean
    },
  ) {
    super(message)
    this.name = 'ApiClientError'
    this.code = options.code
    this.status = options.status
    this.details = options.details
    this.traceId = options.traceId
    this.retryable = options.retryable
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'NetworkError'
  }
}

export class TimeoutError extends Error {
  constructor(message = 'Request timed out') {
    super(message)
    this.name = 'TimeoutError'
  }
}

export interface RequestOptions {
  method?: string
  headers?: Record<string, string>
  body?: BodyInit | null
  timeoutMs?: number
  signal?: AbortSignal
}

function getBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (configured === '' || configured === '/') {
    // Same-origin (Compose nginx proxy or relative deployments).
    return ''
  }
  return (configured || DEFAULT_BASE_URL).replace(/\/$/, '')
}

function getAuthHeaders(): Record<string, string> {
  const token = import.meta.env.VITE_API_AUTH_TOKEN
  if (!token) {
    return {}
  }
  return {
    Authorization: `Bearer ${token}`,
    'X-API-Key': token,
  }
}

async function parseErrorResponse(response: Response): Promise<ApiClientError> {
  let body: ApiErrorBody | null = null
  try {
    body = (await response.json()) as ApiErrorBody
  } catch {
    // non-JSON error body
  }

  if (body?.error) {
    return new ApiClientError(body.error.message, {
      code: body.error.code,
      status: response.status,
      details: body.error.details,
      traceId: body.error.trace_id,
      retryable: body.error.retryable,
    })
  }

  return new ApiClientError(response.statusText || 'Request failed', {
    code: 'HTTP_ERROR',
    status: response.status,
    retryable: response.status >= 500 || response.status === 429,
  })
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const url = `${getBaseUrl()}${path.startsWith('/') ? path : `/${path}`}`
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  const onAbort = () => controller.abort()
  options.signal?.addEventListener('abort', onAbort)

  try {
    const response = await fetch(url, {
      method: options.method ?? 'GET',
      headers: {
        Accept: 'application/json',
        ...getAuthHeaders(),
        ...options.headers,
      },
      body: options.body,
      signal: controller.signal,
    })

    if (!response.ok) {
      throw await parseErrorResponse(response)
    }

    if (response.status === 204) {
      return undefined as T
    }

    const contentType = response.headers.get('content-type') ?? ''
    if (!contentType.includes('application/json')) {
      const text = await response.text()
      return text as T
    }

    return (await response.json()) as T
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      if (options.signal?.aborted) {
        throw error
      }
      throw new TimeoutError()
    }
    throw new NetworkError(
      error instanceof Error ? error.message : 'Network request failed',
    )
  } finally {
    clearTimeout(timeoutId)
    options.signal?.removeEventListener('abort', onAbort)
  }
}

export function getApiBaseUrl(): string {
  return getBaseUrl()
}
