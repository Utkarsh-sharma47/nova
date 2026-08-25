import { useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiClientError, createCustomer, getOpsSummary } from '../api'
import type { DecisionKind, DocumentListItem } from '../api/types'
import { EmptyState } from '../components/EmptyState'
import { ErrorPanel } from '../components/ErrorPanel'
import { LoadingState } from '../components/LoadingState'
import { StatusBadge } from '../components/StatusBadge'
import { useAsync } from '../hooks/useAsync'
import { readStoredCustomerId, storeCustomerId } from '../utils/customer'
import { formatTimestamp, shortId } from '../utils/status'
import { isUuid } from '../utils/uuid'

interface MetricCardProps {
  label: string
  value: number
  tone?: 'neutral' | 'processing' | 'success' | 'danger' | 'warning'
  hint?: string
}

function MetricCard({ label, value, tone = 'neutral', hint }: MetricCardProps) {
  return (
    <article className={`stat-card stat-card--${tone}`}>
      <div className="stat-card__label">{label}</div>
      <div className="stat-card__value">{value}</div>
      {hint ? <div className="stat-card__hint">{hint}</div> : null}
    </article>
  )
}

export function DashboardPage() {
  const [customerId, setCustomerId] = useState(readStoredCustomerId)
  const [draftCustomerId, setDraftCustomerId] = useState(customerId)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<Error | null>(null)
  const [customerFieldError, setCustomerFieldError] = useState<string | null>(
    null,
  )

  const loadSummary = useCallback(async () => {
    if (!customerId.trim()) {
      throw new Error('Enter a customer UUID to load dashboard totals.')
    }
    return getOpsSummary(customerId.trim())
  }, [customerId])

  const summaryState = useAsync(loadSummary, [customerId], {
    enabled: Boolean(customerId.trim()),
  })

  const decisionByDocument = useMemo(() => {
    const map = new Map<string, DecisionKind>()
    if (summaryState.status !== 'success') {
      return map
    }
    for (const item of summaryState.data.recent_decisions) {
      map.set(item.document_id, item.decision)
    }
    return map
  }, [summaryState])

  function applyCustomerId() {
    const next = draftCustomerId.trim()
    if (!next) {
      setCustomerFieldError('Customer ID is required.')
      return
    }
    if (!isUuid(next)) {
      setCustomerFieldError('Enter a valid customer UUID.')
      return
    }
    setCustomerFieldError(null)
    storeCustomerId(next)
    setCustomerId(next)
  }

  async function handleCreateCustomer() {
    setCreateError(null)
    setCustomerFieldError(null)
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
      <header className="page-header">
        <h1 className="page-header__title">Operations dashboard</h1>
        <p className="page-header__subtitle">
          Live verification totals for a customer. Counts come from the Nova
          ops summary API — nothing is invented in the browser.
        </p>
      </header>

      <section className="panel" aria-labelledby="customer-scope-heading">
        <div className="panel__header">
          <h2 id="customer-scope-heading">Customer scope</h2>
        </div>
        <div className="form-row">
          <label htmlFor="dashboard-customer-id">Customer ID (UUID)</label>
          <input
            id="dashboard-customer-id"
            value={draftCustomerId}
            onChange={(event) => {
              setDraftCustomerId(event.target.value)
              setCustomerFieldError(null)
            }}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                applyCustomerId()
              }
            }}
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            autoComplete="off"
            spellCheck={false}
            aria-invalid={customerFieldError ? true : undefined}
            aria-describedby={
              customerFieldError ? 'dashboard-customer-error' : undefined
            }
          />
          {customerFieldError ? (
            <p id="dashboard-customer-error" className="form-error-text">
              {customerFieldError}
            </p>
          ) : (
            <p className="form-hint">
              Use an existing customer UUID, or create a demo customer to bootstrap
              local ops.
            </p>
          )}
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
          {summaryState.status === 'success' ? (
            <button
              type="button"
              className="btn btn--ghost"
              onClick={() => summaryState.reload()}
            >
              Refresh
            </button>
          ) : null}
        </div>
      </section>

      {createError ? (
        <ErrorPanel
          title="Could not create customer"
          message={createError.message}
          traceId={
            createError instanceof ApiClientError ? createError.traceId : undefined
          }
          code={createError instanceof ApiClientError ? createError.code : undefined}
          retryable={
            createError instanceof ApiClientError ? createError.retryable : true
          }
          onRetry={() => void handleCreateCustomer()}
        />
      ) : null}

      {!customerId.trim() ? (
        <EmptyState
          title="No customer selected"
          message="Provide a customer UUID or create a demo customer to load operations data."
        />
      ) : null}

      {customerId.trim() &&
      (summaryState.status === 'loading' || summaryState.status === 'idle') ? (
        <LoadingState label="Loading operations summary…" />
      ) : null}

      {summaryState.status === 'error' ? (
        <ErrorPanel
          title="Failed to load dashboard"
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
              : true
          }
          onRetry={() => summaryState.reload()}
        />
      ) : null}

      {summaryState.status === 'success' ? (
        <>
          <p className="section-label">Document pipeline</p>
          <section className="metrics-grid metrics-grid--4" aria-label="Document totals">
            <MetricCard
              label="Total documents"
              value={summaryState.data.totals.documents}
              tone="neutral"
            />
            <MetricCard
              label="Processing"
              value={summaryState.data.totals.processing}
              tone="processing"
            />
            <MetricCard
              label="Processed"
              value={summaryState.data.totals.decided}
              tone="success"
              hint="Status DECIDED"
            />
            <MetricCard
              label="Failed"
              value={summaryState.data.totals.failed}
              tone="danger"
            />
          </section>

          <p className="section-label">Routing decisions</p>
          <section className="metrics-grid metrics-grid--3" aria-label="Decision outcomes">
            <MetricCard
              label="AUTO_APPROVE"
              value={summaryState.data.totals.auto_approve}
              tone="success"
            />
            <MetricCard
              label="HUMAN_REVIEW"
              value={summaryState.data.totals.human_review}
              tone="warning"
            />
            <MetricCard
              label="AMENDMENT_REQUEST"
              value={summaryState.data.totals.amendment_request}
              tone="danger"
            />
          </section>

          <p className="section-label">Validation outcomes</p>
          <section className="metrics-grid metrics-grid--3" aria-label="Validation outcomes">
            <MetricCard
              label="MATCH"
              value={summaryState.data.validation_outcomes?.MATCH ?? 0}
              tone="success"
            />
            <MetricCard
              label="MISMATCH"
              value={summaryState.data.validation_outcomes?.MISMATCH ?? 0}
              tone="danger"
            />
            <MetricCard
              label="UNCERTAIN"
              value={summaryState.data.validation_outcomes?.UNCERTAIN ?? 0}
              tone="warning"
            />
          </section>

          <section className="panel">
            <div className="panel__header">
              <h2>Recent documents</h2>
              <span className="panel__meta">
                Up to 10 · customer {shortId(summaryState.data.customer_id)}
              </span>
            </div>
            {summaryState.data.recent_documents.length === 0 ? (
              <EmptyState
                title="No documents yet"
                message="Upload a document for this customer to see pipeline activity here."
                action={
                  <Link className="btn btn--secondary btn--sm" to="/upload">
                    Go to upload
                  </Link>
                }
              />
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Document ID</th>
                      <th scope="col">Type</th>
                      <th scope="col">Shipment</th>
                      <th scope="col">Status</th>
                      <th scope="col">Decision</th>
                      <th scope="col">Updated</th>
                      <th scope="col">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summaryState.data.recent_documents.map((doc) => (
                      <DocumentRow
                        key={doc.document_id}
                        doc={doc}
                        decision={decisionByDocument.get(doc.document_id)}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel__header">
              <h2>Recent decisions</h2>
              <span className="panel__meta">Up to 10 routing dispositions</span>
            </div>
            {summaryState.data.recent_decisions.length === 0 ? (
              <EmptyState
                title="No decisions yet"
                message="Routing decisions appear here after documents complete verification."
              />
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th scope="col">Document</th>
                      <th scope="col">Shipment</th>
                      <th scope="col">Decision</th>
                      <th scope="col">Created</th>
                      <th scope="col">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summaryState.data.recent_decisions.map((item) => (
                      <tr key={item.decision_id}>
                        <td className="id-cell">
                          <Link to={`/documents/${item.document_id}`}>
                            {item.document_id}
                          </Link>
                        </td>
                        <td className="id-cell">
                          <Link to={`/shipments/${item.shipment_id}`}>
                            {item.shipment_id}
                          </Link>
                        </td>
                        <td>
                          <StatusBadge status={item.decision} />
                        </td>
                        <td>{formatTimestamp(item.created_at)}</td>
                        <td className="cell-actions">
                          <Link
                            className="btn btn--secondary btn--sm"
                            to={`/documents/${item.document_id}`}
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <p className="form-hint">
            Trace ID: <code className="mono">{summaryState.data.trace_id}</code>
          </p>
        </>
      ) : null}
    </>
  )
}

function DocumentRow({
  doc,
  decision,
}: {
  doc: DocumentListItem
  decision?: DecisionKind
}) {
  return (
    <tr>
      <td className="id-cell">
        <Link to={`/documents/${doc.document_id}`}>{doc.document_id}</Link>
      </td>
      <td>{doc.document_type ?? '—'}</td>
      <td className="id-cell">
        {doc.shipment_id ? (
          <Link to={`/shipments/${doc.shipment_id}`}>{doc.shipment_id}</Link>
        ) : (
          '—'
        )}
      </td>
      <td>
        <StatusBadge status={doc.status} showLifecycle />
      </td>
      <td>{decision ? <StatusBadge status={decision} /> : '—'}</td>
      <td>{formatTimestamp(doc.updated_at)}</td>
      <td className="cell-actions">
        <Link
          className="btn btn--secondary btn--sm"
          to={`/documents/${doc.document_id}`}
        >
          View
        </Link>
      </td>
    </tr>
  )
}
