import { apiRequest } from './client'
import type { CreateCustomerResponse, OpsSummary } from './types'

export function getOpsSummary(customerId: string): Promise<OpsSummary> {
  const search = new URLSearchParams({ customer_id: customerId })
  return apiRequest<OpsSummary>(`/v1/ops/summary?${search.toString()}`)
}

export function createCustomer(name: string): Promise<CreateCustomerResponse> {
  return apiRequest<CreateCustomerResponse>('/v1/customers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}
