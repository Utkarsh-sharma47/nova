import type { DecisionKind, DecisionResult } from '../api/types'
import { formatTimestamp } from '../utils/status'
import { StatusBadge } from './StatusBadge'

interface DecisionPanelProps {
  decision: DecisionResult | null
  loading?: boolean
  notAvailableMessage?: string
}

export function DecisionPanel({
  decision,
  loading = false,
  notAvailableMessage = 'Decision not yet available.',
}: DecisionPanelProps) {
  if (loading) {
    return <p role="status">Loading decision…</p>
  }

  if (!decision) {
    return <p className="form-hint">{notAvailableMessage}</p>
  }

  const isAttention =
    decision.decision === 'HUMAN_REVIEW' ||
    decision.decision === 'AMENDMENT_REQUEST'

  return (
    <section
      className={isAttention ? 'panel panel--highlight' : 'panel'}
      aria-labelledby="decision-heading"
    >
      <h2 id="decision-heading">Routing decision</h2>
      <dl className="meta-list">
        <dt>Decision</dt>
        <dd>
          <StatusBadge status={decision.decision as DecisionKind} />
        </dd>
        <dt>Decision ID</dt>
        <dd>{decision.decision_id}</dd>
        <dt>Created</dt>
        <dd>{formatTimestamp(decision.created_at)}</dd>
        {decision.policy_version ? (
          <>
            <dt>Policy</dt>
            <dd>{decision.policy_version}</dd>
          </>
        ) : null}
        {decision.approval_state ? (
          <>
            <dt>Approval state</dt>
            <dd>{decision.approval_state}</dd>
          </>
        ) : null}
      </dl>
      {decision.rationale ? (
        <p>
          <strong>Rationale:</strong> {decision.rationale}
        </p>
      ) : null}
      {decision.inputs ? (
        <details>
          <summary>Decision inputs</summary>
          <pre
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8125rem',
              overflow: 'auto',
            }}
          >
            {JSON.stringify(decision.inputs, null, 2)}
          </pre>
        </details>
      ) : null}
    </section>
  )
}
