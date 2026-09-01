import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiClientError, NetworkError, submitQuery, TimeoutError } from '../api'
import type { QueryResponse } from '../api/types'
import { EmptyState } from '../components/EmptyState'
import { ErrorPanel } from '../components/ErrorPanel'
import { LoadingState } from '../components/LoadingState'
import { StatusBadge } from '../components/StatusBadge'
import { readStoredCustomerId, storeCustomerId } from '../utils/customer'
import { formatConfidence } from '../utils/status'
import { isUuid } from '../utils/uuid'

const EXAMPLE_QUERIES = [
  {
    label: 'How many strong agreement documents are there?',
    question: 'How many strong agreement documents are there?',
  },
  {
    label: 'How many weak agreement documents are there?',
    question: 'How many weak agreement documents are there?',
  },
  {
    label: 'Show strong agreement documents.',
    question: 'Show strong agreement documents.',
  },
  {
    label: 'Show weak agreement documents.',
    question: 'Show weak agreement documents.',
  },
  {
    label: 'How many documents are there?',
    question: 'How many documents are there?',
  },
  {
    label: 'Show documents with confidence below 70%.',
    question: 'Show documents with confidence below 70%.',
  },
  {
    label: 'Which documents have mismatches?',
    question: 'Which documents have mismatches?',
  },
  {
    label: 'How many documents need human review?',
    question: 'How many documents need human review?',
  },
  {
    label: 'How many documents were auto-approved?',
    question: 'How many documents were auto-approved?',
  },
  {
    label: 'How many documents were processed this week?',
    question: 'How many documents were processed this week?',
  },
  {
    label: 'How many documents require attention?',
    question: 'How many documents require attention?',
  },
  {
    label: 'How many shipments are in human review?',
    question: 'How many shipments are in human review?',
  },
  {
    label: 'Show documents for this shipment',
    question: 'Show documents for this shipment',
    needsShipment: true,
  },
  {
    label: 'What is the decision for this document?',
    question: 'What is the decision for this document?',
    needsDocument: true,
  },
] as const

const SUPPORTED_INTENTS = [
  'get_shipment — fetch shipment by id',
  'get_document — fetch document + status by id',
  'get_document_validation — validation outcome for a document',
  'get_document_decision — router decision for a document',
  'list_shipments_by_decision — filter by AUTO_APPROVE | HUMAN_REVIEW | AMENDMENT_REQUEST',
  'list_documents_for_shipment — documents for a shipment',
  'summarize_run — summarize extraction/validation/decision for a run_id',
  'count_documents_by_agreement — count STRONG / PARTIAL / WEAK agreement docs',
  'list_documents_by_agreement — list documents by agreement category',
  'count_documents_requiring_attention — partial + weak agreement count',
  'count_documents_by_decision — count by AUTO_APPROVE / HUMAN_REVIEW / AMENDMENT_REQUEST',
  'count_documents_with_mismatches — count documents with validation MISMATCH',
  'count_documents — total documents (optionally within a time window)',
  'count_shipments — total shipments (optionally within a time window)',
  'list_shipments — shipments for the current customer',
  'list_recent_documents — most recently updated documents',
  'list_documents_by_decision — documents routed to a given disposition',
  'list_documents_by_confidence — documents below a confidence threshold, or lowest first',
  'list_documents_with_mismatches — documents whose validation result is MISMATCH',
  'list_documents_with_uncertain_validation — documents with UNCERTAIN validation',
  'get_document_mismatched_fields — which fields mismatched for one document',
  'explain_document_review — validation + decision reasoning for one document',
  'compare_agreement — STRONG / PARTIAL / WEAK breakdown',
]

function recordHasStatus(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0
}

function recordCount(record: Record<string, unknown>): number | null {
  const raw = record.count
  return typeof raw === 'number' ? raw : null
}

function confidenceDisplay(record: Record<string, unknown>): string {
  const percent = record.document_confidence_percent
  if (typeof percent === 'number') {
    return `${percent}%`
  }
  const score = record.document_confidence
  if (typeof score === 'number') {
    return formatConfidence(score)
  }
  return 'Confidence unavailable'
}

function extractionDisplay(record: Record<string, unknown>): string | null {
  const percent = record.extraction_confidence_percent
  if (typeof percent === 'number') {
    return `${percent}%`
  }
  const score = record.extraction_confidence
  if (typeof score === 'number') {
    return formatConfidence(score)
  }
  return null
}

function stringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter((item): item is string => typeof item === 'string')
}

function recordDetails(record: Record<string, unknown>): string[] {
  const lines: string[] = []
  const mismatches = record.mismatches
  if (Array.isArray(mismatches)) {
    for (const item of mismatches) {
      if (item && typeof item === 'object' && 'field' in item) {
        const field = String((item as { field?: unknown }).field ?? '—')
        const detail =
          (item as { reason_detail?: unknown; reason_code?: unknown })
            .reason_detail ??
          (item as { reason_code?: unknown }).reason_code ??
          '—'
        lines.push(`${field} — ${String(detail)}`)
      }
    }
  }
  const mismatchedFields = stringList(record.mismatched_fields)
  if (mismatchedFields.length > 0 && lines.length === 0) {
    lines.push(...mismatchedFields.map((field) => `${field} — MISMATCH`))
  }
  const uncertainFields = stringList(record.uncertain_fields)
  for (const field of uncertainFields) {
    lines.push(`${field} — UNCERTAIN`)
  }
  const rationale = record.rationale
  if (typeof rationale === 'string' && rationale.trim()) {
    lines.push(`Rationale: ${rationale}`)
  }
  return lines
}

export function QueryPage() {
  const [question, setQuestion] = useState('')
  const [customerId, setCustomerId] = useState(readStoredCustomerId)
  const [shipmentId, setShipmentId] = useState('')
  const [documentId, setDocumentId] = useState('')
  const [runId, setRunId] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [clientError, setClientError] = useState<string | null>(null)
  const requestSeq = useRef(0)

  // Keep customer scope aligned with dashboard/upload when returning to this page.
  useEffect(() => {
    const syncCustomer = () => {
      const stored = readStoredCustomerId()
      if (stored) {
        setCustomerId(stored)
      }
    }
    syncCustomer()
    window.addEventListener('focus', syncCustomer)
    return () => window.removeEventListener('focus', syncCustomer)
  }, [])

  function validateInputs(
    questionText: string,
    options?: { requireShipment?: boolean; requireDocument?: boolean },
  ): string | null {
    if (!questionText.trim()) {
      return 'Question is required.'
    }
    if (!customerId.trim()) {
      return 'Customer ID is required. Create or load a customer on the Dashboard first.'
    }
    if (!isUuid(customerId.trim())) {
      return 'Customer ID must be a valid UUID.'
    }
    if (shipmentId.trim() && !isUuid(shipmentId.trim())) {
      return 'Shipment ID must be a valid UUID when provided.'
    }
    if (documentId.trim() && !isUuid(documentId.trim())) {
      return 'Document ID must be a valid UUID when provided.'
    }
    if (runId.trim() && !isUuid(runId.trim())) {
      return 'Run ID must be a valid UUID when provided.'
    }
    if (options?.requireShipment && !shipmentId.trim()) {
      return 'This example needs a shipment ID in the scope fields below.'
    }
    if (options?.requireDocument && !documentId.trim()) {
      return 'This example needs a document ID in the scope fields below.'
    }
    return null
  }

  async function runQuery(questionOverride?: string) {
    const questionText = (questionOverride ?? question).trim()
    const validationError = validateInputs(questionText)
    setClientError(validationError)
    setError(null)
    setResponse(null)
    if (validationError) {
      return
    }

    const seq = ++requestSeq.current
    storeCustomerId(customerId.trim())
    setLoading(true)
    try {
      const result = await submitQuery({
        question: questionText,
        customer_id: customerId.trim(),
        scope: {
          shipment_id: shipmentId.trim() || null,
          document_id: documentId.trim() || null,
          run_id: runId.trim() || null,
        },
      })
      if (seq !== requestSeq.current) {
        return
      }
      setResponse(result)
    } catch (err) {
      if (seq !== requestSeq.current) {
        return
      }
      setError(err instanceof Error ? err : new Error(String(err)))
    } finally {
      if (seq === requestSeq.current) {
        setLoading(false)
      }
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    await runQuery()
  }

  async function applyExample(example: (typeof EXAMPLE_QUERIES)[number]) {
    setQuestion(example.question)
    setClientError(null)
    setError(null)
    setResponse(null)

    const needsShipment = 'needsShipment' in example && example.needsShipment
    const needsDocument = 'needsDocument' in example && example.needsDocument
    const validationError = validateInputs(example.question, {
      requireShipment: needsShipment,
      requireDocument: needsDocument,
    })
    if (validationError) {
      setClientError(validationError)
      return
    }
    await runQuery(example.question)
  }

  return (
    <>
      <header className="page-header">
        <h1 className="page-header__title">Operations query</h1>
        <p className="page-header__subtitle">
          Search persisted verification data through allow-listed intents. Questions
          outside the supported set return UNSUPPORTED — this is not an open-ended
          LLM chat.
        </p>
      </header>

      <section className="panel">
        <div className="panel__header">
          <h2>Example questions</h2>
        </div>
        <p className="form-hint">
          Click an example to run it immediately when a valid customer ID is set.
          Add scope IDs when the intent requires them.
        </p>
        <div className="example-queries" role="list">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example.label}
              type="button"
              className="example-chip"
              role="listitem"
              onClick={() => void applyExample(example)}
            >
              {example.label}
            </button>
          ))}
        </div>
      </section>

      <details className="panel">
        <summary>
          <strong>Supported intents</strong>
        </summary>
        <ul className="intent-list">
          {SUPPORTED_INTENTS.map((intent) => (
            <li key={intent}>{intent}</li>
          ))}
        </ul>
      </details>

      <form className="panel" onSubmit={handleSubmit} noValidate>
        <div className="panel__header">
          <h2>Query</h2>
        </div>
        <div className="form-row">
          <label htmlFor="query-question">Question</label>
          <textarea
            id="query-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            required
            disabled={loading}
            placeholder="e.g. How many strong agreement documents are there?"
          />
        </div>
        <div className="form-row">
          <label htmlFor="query-customer-id">Customer ID</label>
          <input
            id="query-customer-id"
            value={customerId}
            onChange={(event) => setCustomerId(event.target.value)}
            required
            spellCheck={false}
            autoComplete="off"
            disabled={loading}
          />
          <p className="form-hint">
            Queries are scoped to this customer. Use the same ID shown on the{' '}
            <Link to="/">Dashboard</Link> after upload.
          </p>
        </div>
        <div className="form-grid">
          <div className="form-row">
            <label htmlFor="query-shipment-id">Shipment ID (optional)</label>
            <input
              id="query-shipment-id"
              value={shipmentId}
              onChange={(event) => setShipmentId(event.target.value)}
              spellCheck={false}
              autoComplete="off"
              disabled={loading}
            />
          </div>
          <div className="form-row">
            <label htmlFor="query-document-id">Document ID (optional)</label>
            <input
              id="query-document-id"
              value={documentId}
              onChange={(event) => setDocumentId(event.target.value)}
              spellCheck={false}
              autoComplete="off"
              disabled={loading}
            />
          </div>
        </div>
        <div className="form-row">
          <label htmlFor="query-run-id">Run ID (optional)</label>
          <input
            id="query-run-id"
            value={runId}
            onChange={(event) => setRunId(event.target.value)}
            spellCheck={false}
            autoComplete="off"
            disabled={loading}
          />
        </div>
        {clientError ? (
          <ErrorPanel title="Validation error" message={clientError} />
        ) : null}
        <div className="button-row">
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Querying…' : 'Submit query'}
          </button>
        </div>
      </form>

      {loading ? <LoadingState label="Running query…" /> : null}

      {error ? (
        <ErrorPanel
          title={
            error instanceof TimeoutError
              ? 'Request timed out'
              : error instanceof NetworkError
                ? 'Network error'
                : 'Query request failed'
          }
          message={error.message}
          code={error instanceof ApiClientError ? error.code : undefined}
          traceId={error instanceof ApiClientError ? error.traceId : undefined}
          retryable={
            error instanceof ApiClientError
              ? error.retryable
              : error instanceof NetworkError || error instanceof TimeoutError
          }
          onRetry={() => void runQuery()}
        />
      ) : null}

      {response ? (
        <section className="panel" aria-live="polite">
          <div className="panel__header">
            <h2>Query result</h2>
            <div className="badge-row">
              <StatusBadge status={response.status} />
            </div>
          </div>

          <dl className="meta-list">
            <dt>Question</dt>
            <dd>{response.question}</dd>
            <dt>Interpreted intent</dt>
            <dd>
              {response.interpreted_intent ? (
                <>
                  <code className="mono">{response.interpreted_intent.name}</code>
                  {' '}
                  (v{response.interpreted_intent.version})
                  {response.interpreted_intent.confidence != null ? (
                    <span className="form-hint">
                      {' '}
                      confidence{' '}
                      {Math.round(response.interpreted_intent.confidence * 100)}%
                    </span>
                  ) : null}
                </>
              ) : (
                '—'
              )}
            </dd>
            <dt>Filters applied</dt>
            <dd>
              {response.interpreted_intent &&
              Object.keys(response.interpreted_intent.parameters ?? {}).length > 0 ? (
                <code className="mono">
                  {JSON.stringify(response.interpreted_intent.parameters)}
                </code>
              ) : (
                'None'
              )}
            </dd>
            <dt>Trace ID</dt>
            <dd>
              <code className="mono">{response.trace_id}</code>
            </dd>
          </dl>

          {response.status === 'RESULT' && response.result ? (
            <>
              <p className="query-summary">
                <strong>Answer:</strong>
              </p>
              <pre className="query-answer">{response.result.answer_summary}</pre>
              {response.result.records.length > 0 ? (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th scope="col">Type</th>
                        <th scope="col">Identifier</th>
                        <th scope="col">Agreement confidence</th>
                        <th scope="col">Extraction</th>
                        <th scope="col">Agreement</th>
                        <th scope="col">Decision / status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {response.result.records.map((record, index) => {
                        const count = recordCount(record)
                        const agreement =
                          typeof record.agreement === 'string'
                            ? record.agreement
                            : null
                        const invoice =
                          typeof record.invoice_number === 'string'
                            ? record.invoice_number
                            : null
                        const details = recordDetails(record)
                        const extraction = extractionDisplay(record)
                        return (
                          <tr key={`record-${index}`}>
                            <td>{String(record.type ?? 'record')}</td>
                            <td className="id-cell">
                              {count != null ? (
                                <div>
                                  Count: <strong>{count}</strong>
                                  {agreement ? ` · ${agreement}` : ''}
                                  {typeof record.decision === 'string'
                                    ? ` · ${record.decision}`
                                    : ''}
                                </div>
                              ) : null}
                              {invoice ? <div>Invoice: {invoice}</div> : null}
                              {'document_id' in record && record.document_id ? (
                                <div>
                                  Document:{' '}
                                  <Link
                                    to={`/documents/${String(record.document_id)}`}
                                  >
                                    {String(record.document_id)}
                                  </Link>
                                </div>
                              ) : null}
                              {'shipment_id' in record && record.shipment_id ? (
                                <div>
                                  Shipment:{' '}
                                  <Link
                                    to={`/shipments/${String(record.shipment_id)}`}
                                  >
                                    {String(record.shipment_id)}
                                  </Link>
                                </div>
                              ) : null}
                              {'run_id' in record && record.run_id ? (
                                <div>Run: {String(record.run_id)}</div>
                              ) : null}
                              {details.length > 0 ? (
                                <ul className="record-detail-list">
                                  {details.map((line) => (
                                    <li key={line}>{line}</li>
                                  ))}
                                </ul>
                              ) : null}
                              {count == null &&
                              !invoice &&
                              !record.document_id &&
                              !record.shipment_id &&
                              !record.run_id &&
                              details.length === 0
                                ? '—'
                                : null}
                            </td>
                            <td>
                              {record.type === 'document' ||
                              record.document_confidence != null ||
                              record.document_confidence_percent != null
                                ? confidenceDisplay(record)
                                : '—'}
                            </td>
                            <td>{extraction ?? '—'}</td>
                            <td>
                              {agreement ? (
                                <StatusBadge status={agreement} />
                              ) : (
                                '—'
                              )}
                            </td>
                            <td>
                              <div className="badge-row">
                                {recordHasStatus(record.decision) ? (
                                  <StatusBadge status={record.decision} />
                                ) : null}
                                {recordHasStatus(record.status) ? (
                                  <StatusBadge status={record.status} />
                                ) : null}
                                {recordHasStatus(record.overall_result) ? (
                                  <StatusBadge status={record.overall_result} />
                                ) : null}
                                {recordHasStatus(record.validation_result) ? (
                                  <StatusBadge
                                    status={record.validation_result}
                                  />
                                ) : null}
                                {!record.decision &&
                                !record.status &&
                                !record.overall_result &&
                                !record.validation_result &&
                                count == null
                                  ? '—'
                                  : null}
                              </div>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState
                  title="No record rows"
                  message="The query returned a summary without individual records."
                />
              )}
            </>
          ) : null}

          {response.status === 'EMPTY' && response.result?.answer_summary ? (
            <>
              <p className="query-summary">
                <strong>Answer:</strong>
              </p>
              <pre className="query-answer">{response.result.answer_summary}</pre>
            </>
          ) : null}

          {response.status === 'EMPTY' && !response.result?.answer_summary ? (
            <EmptyState
              title="No matching records"
              message="The query succeeded but found no matching records."
            />
          ) : null}

          {response.status === 'UNSUPPORTED' && response.unsupported ? (
            <section className="panel panel--highlight">
              <h3>Unsupported query</h3>
              <p>{response.unsupported.message}</p>
              <p>
                <strong>Reason:</strong>{' '}
                <code className="mono">{response.unsupported.reason_code}</code>
              </p>
              {response.unsupported.suggestions?.length ? (
                <>
                  <p>
                    <strong>Suggestions:</strong>
                  </p>
                  <ul>
                    {response.unsupported.suggestions.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </>
              ) : null}
            </section>
          ) : null}

          {response.status === 'FAILURE' && response.failure ? (
            <ErrorPanel
              title="Query failure"
              message={response.failure.message}
              code={response.failure.code}
              traceId={response.trace_id}
              retryable={response.failure.retryable}
              onRetry={
                response.failure.retryable ? () => void runQuery() : undefined
              }
            />
          ) : null}
        </section>
      ) : null}
    </>
  )
}
