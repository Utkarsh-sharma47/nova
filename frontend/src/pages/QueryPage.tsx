import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiClientError, NetworkError, submitQuery, TimeoutError } from '../api'
import type { QueryResponse } from '../api/types'
import { ErrorPanel } from '../components/ErrorPanel'
import { LoadingState } from '../components/LoadingState'
import { StatusBadge } from '../components/StatusBadge'

const SUPPORTED_INTENTS = [
  'get_shipment — fetch shipment by id',
  'get_document — fetch document + status by id',
  'get_document_validation — validation outcome for a document',
  'get_document_decision — router decision for a document',
  'list_shipments_by_decision — filter by AUTO_APPROVE | HUMAN_REVIEW | AMENDMENT_REQUEST',
  'list_documents_for_shipment — documents for a shipment',
  'summarize_run — summarize extraction/validation/decision for a run_id',
]

const STORAGE_KEY = 'nova.customer_id'

function readStoredCustomerId(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
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

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
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

  return (
    <>
      <h1>Grounded query</h1>
      <p className="form-hint">
        Ask questions mapped to allow-listed intents over persisted Nova data.
        Arbitrary natural language outside supported intents returns UNSUPPORTED.
      </p>

      <section className="panel">
        <h2>Supported intents</h2>
        <ul className="intent-list">
          {SUPPORTED_INTENTS.map((intent) => (
            <li key={intent}>{intent}</li>
          ))}
        </ul>
      </section>

      <form className="panel" onSubmit={handleSubmit} noValidate>
        <div className="form-row">
          <label htmlFor="query-question">Question</label>
          <textarea
            id="query-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="query-customer-id">Customer ID</label>
          <input
            id="query-customer-id"
            value={customerId}
            onChange={(event) => setCustomerId(event.target.value)}
            required
          />
        </div>
        <div className="form-row">
          <label htmlFor="query-shipment-id">Scope: shipment ID (optional)</label>
          <input
            id="query-shipment-id"
            value={shipmentId}
            onChange={(event) => setShipmentId(event.target.value)}
          />
        </div>
        <div className="form-row">
          <label htmlFor="query-document-id">Scope: document ID (optional)</label>
          <input
            id="query-document-id"
            value={documentId}
            onChange={(event) => setDocumentId(event.target.value)}
          />
        </div>
        <div className="form-row">
          <label htmlFor="query-run-id">Scope: run ID (optional)</label>
          <input
            id="query-run-id"
            value={runId}
            onChange={(event) => setRunId(event.target.value)}
          />
        </div>
        {clientError ? (
          <ErrorPanel title="Validation error" message={clientError} />
        ) : null}
        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Querying…' : 'Submit query'}
        </button>
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
            error instanceof ApiClientError ? error.retryable : undefined
          }
        />
      ) : null}

      {response ? (
        <section className="panel" aria-live="polite">
          <h2>
            Query result{' '}
            <StatusBadge status={response.status} />
          </h2>
          <p>
            <strong>Question:</strong> {response.question}
          </p>
          {response.interpreted_intent ? (
            <p>
              <strong>Intent:</strong> {response.interpreted_intent.name}{' '}
              (v{response.interpreted_intent.version})
            </p>
          ) : null}

          {response.status === 'RESULT' && response.result ? (
            <>
              <p>{response.result.answer_summary}</p>
              {response.result.records.length > 0 ? (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Type</th>
                      <th scope="col">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {response.result.records.map((record, index) => (
                      <tr key={`record-${index}`}>
                        <td>{String(record.type ?? 'record')}</td>
                        <td>
                          {'document_id' in record && record.document_id ? (
                            <div>
                              Document:{' '}
                              <Link to={`/documents/${String(record.document_id)}`}>
                                {String(record.document_id)}
                              </Link>
                            </div>
                          ) : null}
                          {'shipment_id' in record && record.shipment_id ? (
                            <div>
                              Shipment:{' '}
                              <Link to={`/shipments/${String(record.shipment_id)}`}>
                                {String(record.shipment_id)}
                              </Link>
                            </div>
                          ) : null}
                          {'decision' in record && record.decision ? (
                            <div>
                              Decision:{' '}
                              <StatusBadge
                                status={String(record.decision) as 'HUMAN_REVIEW'}
                              />
                            </div>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}
            </>
          ) : null}

          {response.status === 'EMPTY' && response.result ? (
            <p>{response.result.answer_summary}</p>
          ) : null}

          {response.status === 'UNSUPPORTED' && response.unsupported ? (
            <section className="panel panel--highlight">
              <p>{response.unsupported.message}</p>
              <p>
                <strong>Reason:</strong> {response.unsupported.reason_code}
              </p>
              {response.unsupported.suggestions?.length ? (
                <ul>
                  {response.unsupported.suggestions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
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
            />
          ) : null}

          <p className="form-hint">Trace ID: {response.trace_id}</p>
        </section>
      ) : null}
    </>
  )
}
