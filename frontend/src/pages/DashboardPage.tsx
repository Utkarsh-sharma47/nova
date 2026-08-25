import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiClientError, createCustomer, getOpsSummary } from '../api'
import { EmptyState } from '../components/EmptyState'
import { ErrorPanel } from '../components/ErrorPanel'
import { LoadingState } from '../components/LoadingState'
import { StatusBadge } from '../components/StatusBadge'
import { useAsync } from '../hooks/useAsync'
import { formatTimestamp } from '../utils/status'

const STORAGE_KEY = 'nova.customer_id'

function readStoredCustomerId(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
}

function storeCustomerId(value: string): void {
  try {
    if (value) {
      sessionStorage.setItem(STORAGE_KEY, value)
    }
  } catch {
    // Ignore storage failures in restricted contexts.
  }
}

export function DashboardPage() {
  const [customerId, setCustomerId] = useState(readStoredCustomerId)
  const [draftCustomerId, setDraftCustomerId] = useState(customerId)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<Error | null>(null)

  const loadSummary = useCallback(async () => {
    if (!customerId.trim()) {
      throw new Error('Enter a customer UUID to load dashboard totals.')
    }
    return getOpsSummary(customerId.trim())
  }, [customerId])

  const summaryState = useAsync(loadSummary, [customerId], {
    enabled: Boolean(customerId.trim()),
  })

  function applyCustomerId() {
    const next = draftCustomerId.trim()
    storeCustomerId(next)
    setCustomerId(next)
  }

  async function handleCreateCustomer() {
    setCreateError(null)
    setCreating(true)
    try {
      const created = await createCustomer('Demo Customer')
      storeCustomerId(created.customer_id)
      setDraftCustomerId(created.customer_id)
      setCustomerId(created.customer_id)
    } catch (error) {
      setCreateError(error instanceof Error ? error : new Error(String(error)))
    } finally {
      setCreating(false)
    }
  }

  return (
    <>
      <h1>Operations dashboard</h1>
      <section className="panel">
        <div className="form-row">
          <label htmlFor="dashboard-customer-id">Customer ID (UUID)</label>
          <input
            id="dashboard-customer-id"
            value={draftCustomerId}
            onChange={(event) => setDraftCustomerId(event.target.value)}
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            autoComplete="off"
          />
        </div>
        <div className="button-row">
          <button type="button" className="btn" onClick={applyCustomerId}>
            Load dashboard
          </button>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => void handleCreateCustomer()}
            disabled={creating}
          >
            {creating ? 'Creating…' : 'Create demo customer'}
          </button>
        </div>
        <p className="form-hint">
          Counts come from <code>GET /v1/ops/summary</code>. No values are invented
          in the browser.
        </p>
      </section>

      {createError ? (
        <ErrorPanel
          message={createError.message}
          traceId={
            createError instanceof ApiClientError ? createError.traceId : undefined
          }
          code={createError instanceof ApiClientError ? createError.code : undefined}
        />
      ) : null}

      {!customerId.trim() ? (
        <EmptyState message="Provide a customer UUID or create a demo customer." />
      ) : null}

      {customerId.trim() &&
      (summaryState.status === 'loading' || summaryState.status === 'idle') ? (
        <LoadingState label="Loading operations summary…" />
      ) : null}

      {summaryState.status === 'error' ? (
        <ErrorPanel
          message={summaryState.error.message}
          traceId={
            summaryState.error instanceof ApiClientError
              ? summaryState.error.traceId
              : undefined
          }
          code={
            summaryState.error instanceof ApiClientError
              ? summaryState.error.code
              : undefined
          }
          retryable={
            summaryState.error instanceof ApiClientError
              ? summaryState.error.retryable
              : undefined
          }
        />
      ) : null}

      {summaryState.status === 'success' ? (
        <>
          <section className="grid-3" aria-label="Document totals">
            <article className="stat-card">
              <div className="stat-card__label">Documents</div>
              <div className="stat-card__value">
                {summaryState.data.totals.documents}
              </div>
            </article>
            <article className="stat-card">
              <div className="stat-card__label">Processing</div>
              <div className="stat-card__value">
                {summaryState.data.totals.processing}
              </div>
            </article>
            <article className="stat-card">
              <div className="stat-card__label">Processed (decided)</div>
              <div className="stat-card__value">
                {summaryState.data.totals.decided}
              </div>
            </article>
            <article className="stat-card">
              <div className="stat-card__label">Failed</div>
              <div className="stat-card__value">
                {summaryState.data.totals.failed}
              </div>
            </article>
          </section>

          <section className="grid-3" aria-label="Decision outcomes">
            <article className="stat-card">
              <div className="stat-card__label">AUTO_APPROVE</div>
              <div className="stat-card__value">
                {summaryState.data.totals.auto_approve}
              </div>
            </article>
            <article className="stat-card">
              <div className="stat-card__label">HUMAN_REVIEW</div>
              <div className="stat-card__value">
                {summaryState.data.totals.human_review}
              </div>
            </article>
            <article className="stat-card">
              <div className="stat-card__label">AMENDMENT_REQUEST</div>
              <div className="stat-card__value">
                {summaryState.data.totals.amendment_request}
              </div>
            </article>
          </section>

          <section className="grid-3" aria-label="Validation outcomes">
            <article className="stat-card">
              <div className="stat-card__label">MATCH</div>
              <div className="stat-card__value">
                {summaryState.data.validation_outcomes?.MATCH ?? 0}
              </div>
            </article>
            <article className="stat-card">
              <div className="stat-card__label">MISMATCH</div>
              <div className="stat-card__value">
                {summaryState.data.validation_outcomes?.MISMATCH ?? 0}
              </div>
            </article>
            <article className="stat-card">
              <div className="stat-card__label">UNCERTAIN</div>
              <div className="stat-card__value">
                {summaryState.data.validation_outcomes?.UNCERTAIN ?? 0}
              </div>
            </article>
          </section>

          <section className="panel">
            <h2>Recent documents</h2>
            {summaryState.data.recent_documents.length === 0 ? (
              <EmptyState message="No documents found for this customer." />
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th scope="col">Document</th>
                    <th scope="col">Type</th>
                    <th scope="col">Status</th>
                    <th scope="col">Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {summaryState.data.recent_documents.map((doc) => (
                    <tr key={doc.document_id}>
                      <td>
                        <Link to={`/documents/${doc.document_id}`}>
                          {doc.document_id}
                        </Link>
                      </td>
                      <td>{doc.document_type ?? '—'}</td>
                      <td>
                        <StatusBadge status={doc.status} showLifecycle />
                      </td>
                      <td>{formatTimestamp(doc.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="panel">
            <h2>Recent decisions</h2>
            {summaryState.data.recent_decisions.length === 0 ? (
              <EmptyState message="No routing decisions recorded yet." />
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th scope="col">Document</th>
                    <th scope="col">Decision</th>
                    <th scope="col">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {summaryState.data.recent_decisions.map((item) => (
                    <tr key={item.decision_id}>
                      <td>
                        <Link to={`/documents/${item.document_id}`}>
                          {item.document_id}
                        </Link>
                      </td>
                      <td>
                        <StatusBadge status={item.decision} />
                      </td>
                      <td>{formatTimestamp(item.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      ) : null}
    </>
  )
}
