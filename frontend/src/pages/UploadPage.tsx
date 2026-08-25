import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import {
  ApiClientError,
  NetworkError,
  TimeoutError,
  uploadDocument,
} from '../api'
import type { DocumentUploadResponse } from '../api/types'
import { ErrorPanel } from '../components/ErrorPanel'
import { StatusBadge } from '../components/StatusBadge'
import { readStoredCustomerId, storeCustomerId } from '../utils/customer'
import { formatBytes } from '../utils/status'
import { generateIdempotencyKey, isUuid } from '../utils/uuid'

const ACCEPTED_TYPES = [
  'application/pdf',
  'text/plain',
  'image/png',
  'image/jpeg',
]
const ACCEPTED_EXTENSIONS = ['.pdf', '.txt', '.png', '.jpg', '.jpeg']

const WORKFLOW_STEPS = [
  'Customer',
  'Shipment',
  'Document',
  'Upload',
  'Result',
] as const

function hasAcceptedExtension(name: string): boolean {
  const lower = name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext))
}

function fileTypeLabel(file: File): string {
  if (file.type) {
    return file.type
  }
  const lower = file.name.toLowerCase()
  if (lower.endsWith('.pdf')) return 'application/pdf'
  if (lower.endsWith('.txt')) return 'text/plain'
  if (lower.endsWith('.png')) return 'image/png'
  if (lower.endsWith('.jpg') || lower.endsWith('.jpeg')) return 'image/jpeg'
  return 'unknown'
}

export function UploadPage() {
  const [customerId, setCustomerId] = useState(readStoredCustomerId)
  const [shipmentId, setShipmentId] = useState('')
  const [documentType, setDocumentType] = useState('')
  const [idempotencyKey, setIdempotencyKey] = useState(generateIdempotencyKey)
  const [file, setFile] = useState<File | null>(null)
  const [clientError, setClientError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<DocumentUploadResponse | null>(null)
  const [apiError, setApiError] = useState<Error | null>(null)

  const activeStep = useMemo(() => {
    if (result) return 4
    if (uploading) return 3
    if (file) return 2
    if (customerId.trim()) return 1
    return 0
  }, [customerId, file, result, uploading])

  function validateFile(selected: File | null): string | null {
    if (!selected) {
      return 'Select a PDF, plain-text, PNG, or JPEG file.'
    }
    const typeOk =
      !selected.type ||
      ACCEPTED_TYPES.includes(selected.type) ||
      selected.type === 'image/jpg'
    const extOk = hasAcceptedExtension(selected.name)
    if (!typeOk && !extOk) {
      return 'Only PDF, plain text, PNG, and JPEG files are supported.'
    }
    return null
  }

  function validateForm(): string | null {
    if (!customerId.trim()) {
      return 'Customer ID is required.'
    }
    if (!isUuid(customerId.trim())) {
      return 'Customer ID must be a valid UUID.'
    }
    if (shipmentId.trim() && !isUuid(shipmentId.trim())) {
      return 'Shipment ID must be a valid UUID when provided.'
    }
    if (!idempotencyKey.trim()) {
      return 'Idempotency key is required.'
    }
    if (idempotencyKey.trim().length < 8 || idempotencyKey.trim().length > 128) {
      return 'Idempotency key must be 8–128 characters.'
    }
    return validateFile(file)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setClientError(null)
    setApiError(null)
    setResult(null)

    const validationError = validateForm()
    if (validationError) {
      setClientError(validationError)
      return
    }

    storeCustomerId(customerId.trim())
    setUploading(true)
    try {
      const response = await uploadDocument({
        file: file as File,
        customerId: customerId.trim(),
        shipmentId: shipmentId.trim() || undefined,
        documentType: documentType.trim() || undefined,
        idempotencyKey: idempotencyKey.trim(),
      })
      setResult(response)
    } catch (error) {
      setApiError(error instanceof Error ? error : new Error(String(error)))
    } finally {
      setUploading(false)
    }
  }

  function handleRetry() {
    setApiError(null)
    const form = document.getElementById('upload-form') as HTMLFormElement | null
    form?.requestSubmit()
  }

  function resetForAnotherUpload() {
    setResult(null)
    setApiError(null)
    setClientError(null)
    setFile(null)
    setIdempotencyKey(generateIdempotencyKey())
    const input = document.getElementById('upload-file') as HTMLInputElement | null
    if (input) {
      input.value = ''
    }
  }

  return (
    <>
      <header className="page-header">
        <h1 className="page-header__title">Upload document</h1>
        <p className="page-header__subtitle">
          Submit a trade document for verification. Nova accepts the file,
          queues pipeline processing, and returns identifiers for tracking.
        </p>
      </header>

      <ol className="workflow-steps" aria-label="Upload workflow">
        {WORKFLOW_STEPS.map((label, index) => {
          let className = ''
          if (index < activeStep) className = 'is-done'
          else if (index === activeStep) className = 'is-active'
          return (
            <li key={label} className={className}>
              {label}
            </li>
          )
        })}
      </ol>

      <form
        id="upload-form"
        className="panel"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="panel__header">
          <h2>1–3 · Scope and file</h2>
        </div>

        <div className="form-grid">
          <div className="form-row">
            <label htmlFor="upload-customer-id">Customer ID</label>
            <input
              id="upload-customer-id"
              value={customerId}
              onChange={(event) => setCustomerId(event.target.value)}
              required
              spellCheck={false}
              autoComplete="off"
              disabled={uploading}
            />
            <p className="form-hint">Required UUID for the owning customer.</p>
          </div>
          <div className="form-row">
            <label htmlFor="upload-shipment-id">Shipment ID (optional)</label>
            <input
              id="upload-shipment-id"
              value={shipmentId}
              onChange={(event) => setShipmentId(event.target.value)}
              spellCheck={false}
              autoComplete="off"
              disabled={uploading}
            />
            <p className="form-hint">
              Leave blank to create a new shipment automatically.
            </p>
          </div>
        </div>

        <div className="form-grid">
          <div className="form-row">
            <label htmlFor="upload-document-type">Document type</label>
            <select
              id="upload-document-type"
              value={documentType}
              onChange={(event) => setDocumentType(event.target.value)}
              disabled={uploading}
            >
              <option value="">Auto / UNKNOWN</option>
              <option value="INVOICE">INVOICE</option>
              <option value="BILL_OF_LADING">BILL_OF_LADING</option>
              <option value="OTHER">OTHER</option>
              <option value="UNKNOWN">UNKNOWN</option>
            </select>
          </div>
          <div className="form-row">
            <label htmlFor="upload-idempotency-key">Idempotency key</label>
            <input
              id="upload-idempotency-key"
              value={idempotencyKey}
              onChange={(event) => setIdempotencyKey(event.target.value)}
              required
              spellCheck={false}
              autoComplete="off"
              disabled={uploading}
            />
            <p className="form-hint">
              Auto-generated; reuse the same key to safely replay an identical
              upload.
            </p>
          </div>
        </div>

        <div className="form-row">
          <label htmlFor="upload-file">Document file</label>
          <input
            id="upload-file"
            type="file"
            accept=".pdf,.txt,.png,.jpg,.jpeg,application/pdf,text/plain,image/png,image/jpeg"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null)
              setClientError(null)
              setResult(null)
            }}
            disabled={uploading}
          />
          {file ? (
            <div className="file-chip" aria-live="polite">
              <div>
                <div className="file-chip__name">{file.name}</div>
                <div className="file-chip__meta">
                  Type: {fileTypeLabel(file)} · Size: {formatBytes(file.size)}
                </div>
              </div>
            </div>
          ) : (
            <p className="form-hint">
              Accepted: PDF, plain text, PNG, or JPEG.
            </p>
          )}
        </div>

        {clientError ? (
          <ErrorPanel title="Validation error" message={clientError} />
        ) : null}

        <div className="button-row">
          <button type="submit" className="btn" disabled={uploading}>
            {uploading ? 'Uploading…' : 'Upload document'}
          </button>
          <button
            type="button"
            className="btn btn--secondary"
            disabled={uploading}
            onClick={() => setIdempotencyKey(generateIdempotencyKey())}
          >
            New idempotency key
          </button>
        </div>
      </form>

      {uploading ? (
        <section className="loading-state" role="status" aria-live="polite">
          <span className="loading-state__spinner" aria-hidden="true" />
          <div className="loading-state__copy">
            <p>
              <strong>Upload in progress…</strong>
            </p>
            <p className="form-hint">
              Sending file to Nova and waiting for acceptance.
            </p>
          </div>
        </section>
      ) : null}

      {apiError ? (
        <ErrorPanel
          title={
            apiError instanceof TimeoutError
              ? 'Request timed out'
              : apiError instanceof NetworkError
                ? 'Network error'
                : 'Upload failed'
          }
          message={apiError.message}
          code={
            apiError instanceof ApiClientError ? apiError.code : undefined
          }
          traceId={
            apiError instanceof ApiClientError ? apiError.traceId : undefined
          }
          retryable={
            apiError instanceof ApiClientError
              ? apiError.retryable
              : apiError instanceof NetworkError ||
                apiError instanceof TimeoutError
          }
          onRetry={handleRetry}
        />
      ) : null}

      {result ? (
        <section className="panel panel--success" role="status" aria-live="polite">
          <div className="result-banner">
            <div className="result-banner__icon" aria-hidden="true">
              ✓
            </div>
            <div>
              <h2 className="result-banner__title">
                {result.idempotent_replay
                  ? 'Idempotent replay — existing acceptance returned'
                  : 'Document accepted'}
              </h2>
              <p className="result-banner__body">
                Your document was accepted and queued for processing. Use the
                IDs below to track verification status.
              </p>
            </div>
          </div>

          <dl className="meta-list">
            <dt>Document ID</dt>
            <dd>
              <Link to={`/documents/${result.document_id}`}>
                {result.document_id}
              </Link>
            </dd>
            <dt>Shipment ID</dt>
            <dd>
              <Link to={`/shipments/${result.shipment_id}`}>
                {result.shipment_id}
              </Link>
            </dd>
            <dt>Run ID</dt>
            <dd>
              <code className="mono">{result.run_id}</code>
            </dd>
            <dt>Processing status</dt>
            <dd>
              <StatusBadge status={result.status} showLifecycle />
            </dd>
            <dt>Idempotent replay</dt>
            <dd>
              {result.idempotent_replay
                ? 'Yes — same idempotency key and payload returned the prior acceptance'
                : 'No — this was a new acceptance'}
            </dd>
            <dt>Trace ID</dt>
            <dd>
              <code className="mono">{result.trace_id}</code>
            </dd>
          </dl>

          <div className="button-row button-row--spaced">
            <Link
              className="btn"
              to={`/documents/${result.document_id}`}
            >
              View document
            </Link>
            <Link
              className="btn btn--secondary"
              to={`/shipments/${result.shipment_id}`}
            >
              View shipment
            </Link>
            <button
              type="button"
              className="btn btn--ghost"
              onClick={resetForAnotherUpload}
            >
              Upload another
            </button>
          </div>
        </section>
      ) : null}
    </>
  )
}
