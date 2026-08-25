import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiClientError, NetworkError, submitQuery, TimeoutError } from '../api'
import type { QueryResponse } from '../api/types'
import { EmptyState } from '../components/EmptyState'
import { ErrorPanel } from '../components/ErrorPanel'
import { LoadingState } from '../components/LoadingState'
import { StatusBadge } from '../components/StatusBadge'
import { readStoredCustomerId, storeCustomerId } from '../utils/customer'
import { isUuid } from '../utils/uuid'

const EXAMPLE_QUERIES = [
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
  {
    label: 'Summarize this verification run',
    question: 'Summarize this verification run',
    needsRun: true,
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
]

function recordHasStatus(value: unknown): value is string {
  return typeof value === 'string' && value.length > 0
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
    if ('needsRun' in example && example.needsRun && !runId.trim()) {
      setClientError('This example needs a run ID in the scope fields below.')
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
            placeholder="e.g. How many shipments are in human review?"
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
            <dt>Trace ID</dt>
            <dd>
              <code className="mono">{response.trace_id}</code>
            </dd>
          </dl>

          {response.status === 'RESULT' && response.result ? (
            <>
              <p className="query-summary">
                <strong>Summary:</strong> {response.result.answer_summary}
              </p>
              {response.result.records.length > 0 ? (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th scope="col">Type</th>
                        <th scope="col">IDs</th>
                        <th scope="col">Status / decision</th>
                      </tr>
                    </thead>
                    <tbody>
                      {response.result.records.map((record, index) => (
                        <tr key={`record-${index}`}>
                          <td>{String(record.type ?? 'record')}</td>
                          <td className="id-cell">
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
                            {!record.document_id &&
                            !record.shipment_id &&
                            !record.run_id
                              ? '—'
                              : null}
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
                              {!record.decision &&
                              !record.status &&
                              !record.overall_result
                                ? '—'
                                : null}
                            </div>
                          </td>
                        </tr>
                      ))}
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
