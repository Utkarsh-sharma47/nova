import { useState, type FormEvent } from 'react'
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

  async function runQuery() {
    setClientError(null)
    setError(null)
    setResponse(null)

    if (!question.trim()) {
      setClientError('Question is required.')
      return
    }
    if (!customerId.trim()) {
      setClientError('Customer ID is required.')
      return
    }
    if (!isUuid(customerId.trim())) {
      setClientError('Customer ID must be a valid UUID.')
      return
    }
    if (shipmentId.trim() && !isUuid(shipmentId.trim())) {
      setClientError('Shipment ID must be a valid UUID when provided.')
      return
    }
    if (documentId.trim() && !isUuid(documentId.trim())) {
      setClientError('Document ID must be a valid UUID when provided.')
      return
    }
    if (runId.trim() && !isUuid(runId.trim())) {
      setClientError('Run ID must be a valid UUID when provided.')
      return
    }

    storeCustomerId(customerId.trim())
    setLoading(true)
    try {
      const result = await submitQuery({
        question: question.trim(),
        customer_id: customerId.trim(),
        scope: {
          shipment_id: shipmentId.trim() || null,
          document_id: documentId.trim() || null,
          run_id: runId.trim() || null,
        },
      })
      setResponse(result)
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    await runQuery()
  }

  function applyExample(example: (typeof EXAMPLE_QUERIES)[number]) {
    setQuestion(example.question)
    setClientError(null)
    setError(null)
    setResponse(null)
    if ('needsShipment' in example && example.needsShipment && !shipmentId.trim()) {
      setClientError(
        'This example needs a shipment ID in the scope fields below.',
      )
    }
    if ('needsDocument' in example && example.needsDocument && !documentId.trim()) {
      setClientError(
        'This example needs a document ID in the scope fields below.',
      )
    }
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
          Click an example to fill the question. Add scope IDs when the intent
          requires them.
        </p>
        <div className="example-queries" role="list">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example.label}
              type="button"
              className="example-chip"
              role="listitem"
              onClick={() => applyExample(example)}
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
                        <th scope="col">Confidence</th>
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
                              {count == null &&
                              !invoice &&
                              !record.document_id &&
                              !record.shipment_id &&
                              !record.run_id
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

          {response.status === 'EMPTY' ? (
            <EmptyState
              title="No matching records"
              message={
                response.result?.answer_summary ??
                'The query succeeded but found no matching records.'
              }
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
