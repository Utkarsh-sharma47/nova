import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiClientError, getShipment } from '../api'
import { EmptyState } from '../components/EmptyState'
import { ErrorPanel } from '../components/ErrorPanel'
import { LoadingState } from '../components/LoadingState'
import { StatusBadge } from '../components/StatusBadge'
import { useAsync } from '../hooks/useAsync'
import { formatTimestamp } from '../utils/status'

export function ShipmentPage() {
  const { shipmentId = '' } = useParams()

  const loadShipment = useCallback(
    () => getShipment(shipmentId),
    [shipmentId],
  )

  const shipmentState = useAsync(loadShipment, [shipmentId], {
    enabled: Boolean(shipmentId),
  })

  if (!shipmentId) {
    return <EmptyState message="Shipment ID is required." />
  }

  if (shipmentState.status === 'loading' || shipmentState.status === 'idle') {
    return <LoadingState label="Loading shipment…" />
  }

  if (shipmentState.status === 'error') {
    return (
      <ErrorPanel
        title="Failed to load shipment"
        message={shipmentState.error.message}
        code={
          shipmentState.error instanceof ApiClientError
            ? shipmentState.error.code
            : undefined
        }
        traceId={
          shipmentState.error instanceof ApiClientError
            ? shipmentState.error.traceId
            : undefined
        }
        retryable={
          shipmentState.error instanceof ApiClientError
            ? shipmentState.error.retryable
            : true
        }
        onRetry={() => shipmentState.reload()}
      />
    )
  }

  const shipment = shipmentState.data

  return (
    <>
      <h1>Shipment {shipment.shipment_id}</h1>

      <section className="panel">
        <dl className="meta-list">
          <dt>Customer</dt>
          <dd>{shipment.customer_id}</dd>
          <dt>Status</dt>
          <dd>{shipment.status}</dd>
          <dt>Created</dt>
          <dd>{formatTimestamp(shipment.created_at)}</dd>
          <dt>Updated</dt>
          <dd>{formatTimestamp(shipment.updated_at)}</dd>
          {shipment.latest_decision ? (
            <>
              <dt>Latest decision</dt>
              <dd>
                <StatusBadge status={shipment.latest_decision.decision} /> on{' '}
                <Link to={`/documents/${shipment.latest_decision.document_id}`}>
                  {shipment.latest_decision.document_id}
                </Link>
              </dd>
            </>
          ) : (
            <>
              <dt>Latest decision</dt>
              <dd>—</dd>
            </>
          )}
        </dl>
      </section>

      <section className="panel">
        <h2>Documents</h2>
        {shipment.documents.length === 0 ? (
          <EmptyState message="No documents attached to this shipment." />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Document</th>
                <th scope="col">Type</th>
                <th scope="col">Status</th>
                <th scope="col">Run</th>
              </tr>
            </thead>
            <tbody>
              {shipment.documents.map((doc) => (
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
                  <td>{doc.run_id ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  )
}
