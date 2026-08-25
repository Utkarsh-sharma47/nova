import { apiRequest, getApiBaseUrl } from './client'
import { getRuntimeAuthToken } from '../runtime-config'
import type {
  DocumentDetail,
  DocumentListResponse,
  DocumentUploadResponse,
  DecisionResult,
  ValidationResult,
} from './types'

export interface UploadDocumentParams {
  file: File
  customerId: string
  shipmentId?: string
  documentType?: string
  idempotencyKey: string
}

export function uploadDocument(
  params: UploadDocumentParams,
): Promise<DocumentUploadResponse> {
  const form = new FormData()
  form.append('file', params.file)
  form.append('customer_id', params.customerId)
  if (params.shipmentId) {
    form.append('shipment_id', params.shipmentId)
  }
  if (params.documentType) {
    form.append('document_type', params.documentType)
  }

  return apiRequest<DocumentUploadResponse>('/v1/documents', {
    method: 'POST',
    headers: { 'Idempotency-Key': params.idempotencyKey },
    body: form,
  })
}

export function listDocuments(params: {
  customerId: string
  limit?: number
  agreement?: string
}): Promise<DocumentListResponse> {
  const search = new URLSearchParams({
    customer_id: params.customerId,
    limit: String(params.limit ?? 20),
  })
  if (params.agreement) {
    search.set('agreement', params.agreement)
  }
  return apiRequest<DocumentListResponse>(`/v1/documents?${search.toString()}`)
}

export function getDocument(
  documentId: string,
  includeExtraction = true,
): Promise<DocumentDetail> {
  const search = includeExtraction ? '?include=extraction' : ''
  return apiRequest<DocumentDetail>(`/v1/documents/${documentId}${search}`)
}

export function getDocumentValidation(
  documentId: string,
): Promise<ValidationResult> {
  return apiRequest<ValidationResult>(`/v1/documents/${documentId}/validation`)
}

export function getDocumentDecision(
  documentId: string,
): Promise<DecisionResult> {
  return apiRequest<DecisionResult>(`/v1/documents/${documentId}/decision`)
}

export async function fetchDocumentContentBlob(
  documentId: string,
): Promise<{ blob: Blob; mediaType: string }> {
  const base = getApiBaseUrl()
  const url = `${base}/v1/documents/${documentId}/content`
  const token = getRuntimeAuthToken()
  const headers: Record<string, string> = { Accept: '*/*' }
  if (token) {
    headers.Authorization = `Bearer ${token}`
    headers['X-API-Key'] = token
  }
  const response = await fetch(url, { headers })
  if (!response.ok) {
    throw new Error(`Failed to load document content (${response.status})`)
  }
  const mediaType =
    response.headers.get('content-type')?.split(';')[0]?.trim() ||
    'application/octet-stream'
  const blob = await response.blob()
  return { blob, mediaType }
}
