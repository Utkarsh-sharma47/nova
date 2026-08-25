import { apiRequest } from './client'
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
}): Promise<DocumentListResponse> {
  const search = new URLSearchParams({
    customer_id: params.customerId,
    limit: String(params.limit ?? 20),
  })
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
