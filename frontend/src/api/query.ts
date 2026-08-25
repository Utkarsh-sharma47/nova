import { apiRequest } from './client'
import type { QueryRequest, QueryResponse } from './types'

export function submitQuery(request: QueryRequest): Promise<QueryResponse> {
  return apiRequest<QueryResponse>('/v1/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
}
