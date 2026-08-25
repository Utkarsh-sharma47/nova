import { useState, type FormEvent } from 'react'
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
import { generateIdempotencyKey } from '../utils/uuid'

const ACCEPTED_TYPES = ['application/pdf', 'text/plain']
const STORAGE_KEY = 'nova.customer_id'

function readStoredCustomerId(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
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

  function validateFile(selected: File | null): string | null {
    if (!selected) {
      return 'Select a PDF or plain-text file.'
    }
    if (!ACCEPTED_TYPES.includes(selected.type)) {
      return 'Only application/pdf and text/plain files are supported.'
    }
    return null
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setClientError(null)
    setApiError(null)
    setResult(null)

    if (!customerId.trim()) {
      setClientError('Customer ID is required.')
      return
    }
    if (!idempotencyKey.trim()) {
      setClientError('Idempotency key is required.')
      return
    }

    const fileError = validateFile(file)
    if (fileError) {
      setClientError(fileError)
      return
    }

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

  return (
    <>
      <h1>Upload document</h1>
      <form className="panel" onSubmit={handleSubmit} noValidate>
        <div className="form-row">
          <label htmlFor="upload-customer-id">Customer ID</label>
          <input
            id="upload-customer-id"
            value={customerId}
            onChange={(event) => setCustomerId(event.target.value)}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="upload-shipment-id">Shipment ID (optional)</label>
          <input
            id="upload-shipment-id"
            value={shipmentId}
            onChange={(event) => setShipmentId(event.target.value)}
          />
        </div>
        <div className="form-row">
          <label htmlFor="upload-document-type">Document type (optional)</label>
          <select
            id="upload-document-type"
            value={documentType}
            onChange={(event) => setDocumentType(event.target.value)}
          >
            <option value="">—</option>
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
          />
          <p className="form-hint">
            Auto-generated UUID; override for replay testing.
          </p>
        </div>
        <div className="form-row">
          <label htmlFor="upload-file">File (PDF or plain text)</label>
          <input
            id="upload-file"
            type="file"
            accept=".pdf,.txt,application/pdf,text/plain"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          {file ? (
            <p className="form-hint">
              Selected: {file.name} ({file.type || 'unknown type'},{' '}
              {file.size} bytes)
            </p>
          ) : null}
        </div>
        {clientError ? (
          <ErrorPanel title="Validation error" message={clientError} />
        ) : null}
        <button type="submit" className="btn" disabled={uploading}>
          {uploading ? 'Uploading…' : 'Upload'}
        </button>
      </form>

      {uploading ? (
        <section className="panel" role="status" aria-live="polite">
          Upload in progress…
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
            apiError instanceof ApiClientError ? apiError.retryable : undefined
          }
        />
      ) : null}

      {result ? (
        <section className="panel" role="status">
          <h2>Upload accepted</h2>
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
            <dd>{result.run_id}</dd>
            <dt>Status</dt>
            <dd>
              <StatusBadge status={result.status} showLifecycle />
            </dd>
            <dt>Idempotent replay</dt>
            <dd>{result.idempotent_replay ? 'Yes' : 'No'}</dd>
            <dt>Trace ID</dt>
            <dd>{result.trace_id}</dd>
          </dl>
        </section>
      ) : null}
    </>
  )
}
