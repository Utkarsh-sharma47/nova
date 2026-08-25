export type DocumentStatus =
  | 'ACCEPTED'
  | 'PROCESSING'
  | 'EXTRACTED'
  | 'VALIDATED'
  | 'DECIDED'
  | 'FAILED'

export type LifecycleBadge = 'PROCESSING' | 'PROCESSED' | 'FAILED'

export type ValidationOutcome = 'MATCH' | 'MISMATCH' | 'UNCERTAIN'

export type DecisionKind = 'AUTO_APPROVE' | 'HUMAN_REVIEW' | 'AMENDMENT_REQUEST'

export type AgreementCategory =
  | 'STRONG_AGREEMENT'
  | 'PARTIAL_AGREEMENT'
  | 'WEAK_AGREEMENT'

export type QueryStatus = 'RESULT' | 'EMPTY' | 'UNSUPPORTED' | 'FAILURE'

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
    trace_id?: string
    retryable: boolean
  }
}

export interface HealthResponse {
  status: string
}

export interface DocumentUploadResponse {
  document_id: string
  shipment_id: string
  run_id: string
  status: DocumentStatus
  idempotent_replay: boolean
  trace_id: string
}

export interface DocumentListItem {
  document_id: string
  shipment_id: string
  customer_id: string
  document_type: string | null
  status: DocumentStatus
  run_id: string | null
  created_at: string
  updated_at: string
  agreement?: AgreementCategory | null
  document_confidence?: number | null
  document_confidence_percent?: number | null
  decision?: DecisionKind | null
  validation_result?: ValidationOutcome | null
  invoice_number?: string | null
}

export interface DocumentListResponse {
  items: DocumentListItem[]
  limit: number
  trace_id: string
}

export interface Evidence {
  evidence_id?: string
  text?: string
  page?: number
  bbox?: Record<string, number>
  source?: string
}

export interface ExtractedField {
  name?: string
  field_name?: string
  value: unknown
  presence: string
  confidence: number | null
  uncertainty?: string
  evidence?: Evidence[]
}

export interface ExtractionSummary {
  status: string
  fields: ExtractedField[]
  warnings?: string[]
  errors?: Array<{ code?: string; message?: string }>
}

export interface DocumentDetail {
  document_id: string
  shipment_id: string
  customer_id: string
  document_type: string | null
  status: DocumentStatus
  run_id: string | null
  created_at: string
  updated_at: string
  agreement?: AgreementCategory | null
  document_confidence?: number | null
  document_confidence_percent?: number | null
  content?: {
    media_type: string
    size_bytes: number
    content_sha256?: string
    download_url?: string | null
    filename?: string | null
  }
  extraction?: ExtractionSummary | null
  failures?: Array<{ code?: string; message?: string; stage?: string }>
  links?: {
    validation?: string
    decision?: string
    shipment?: string
  }
  trace_id: string
}

export interface ValidationCheck {
  check_id: string
  rule_id: string
  field_name?: string
  result: ValidationOutcome
  reason: string
  expected?: unknown
  actual?: unknown
  evidence_ids?: string[]
}

export interface ValidationResult {
  validation_id: string
  document_id: string
  shipment_id: string
  run_id: string
  overall_result: ValidationOutcome
  checks: ValidationCheck[]
  created_at: string
  trace_id: string
}

export interface DecisionResult {
  decision_id: string
  document_id: string
  shipment_id: string
  run_id: string
  decision: DecisionKind
  rationale?: string
  policy_version?: string
  inputs?: Record<string, unknown>
  created_at: string
  approval_state?: string
  trace_id: string
}

export interface ShipmentDocumentSummary {
  document_id: string
  document_type: string | null
  status: DocumentStatus
  run_id: string | null
}

export interface ShipmentDetail {
  shipment_id: string
  customer_id: string
  status: string
  document_ids: string[]
  documents: ShipmentDocumentSummary[]
  latest_decision?: {
    document_id: string
    decision: DecisionKind
  } | null
  created_at: string
  updated_at: string
  trace_id: string
}

export interface OpsSummary {
  customer_id: string
  totals: {
    documents: number
    processing: number
    decided: number
    failed: number
    human_review: number
    amendment_request: number
    auto_approve: number
    strong_agreement?: number
    partial_agreement?: number
    weak_agreement?: number
  }
  agreement_outcomes?: {
    STRONG_AGREEMENT: number
    PARTIAL_AGREEMENT: number
    WEAK_AGREEMENT: number
  }
  validation_outcomes?: {
    MATCH: number
    MISMATCH: number
    UNCERTAIN: number
  }
  recent_documents: DocumentListItem[]
  recent_decisions: Array<{
    decision_id: string
    document_id: string
    shipment_id: string
    decision: DecisionKind
    created_at: string
  }>
  trace_id: string
}

export interface CreateCustomerResponse {
  customer_id: string
  name: string
  status: string
  created_at: string
  trace_id: string
}

export interface QueryScope {
  shipment_id?: string | null
  document_id?: string | null
  run_id?: string | null
  time_range?: Record<string, unknown> | null
}

export interface QueryRequest {
  question: string
  customer_id: string
  scope?: QueryScope
  options?: { max_results?: number }
}

export interface InterpretedIntent {
  name: string
  version: string
  parameters: Record<string, unknown>
  confidence?: number | null
}

export interface QueryResponse {
  question: string
  interpreted_intent?: InterpretedIntent | null
  status: QueryStatus
  result?: {
    answer_summary: string
    records: Record<string, unknown>[]
    citations: Array<Record<string, unknown>>
  } | null
  unsupported?: {
    reason_code: string
    message: string
    suggestions?: string[]
  } | null
  failure?: {
    code: string
    message: string
    retryable: boolean
  } | null
  trace_id: string
}
