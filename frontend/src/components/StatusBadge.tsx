import { toLifecycleBadge } from '../utils/status'
import type { DocumentStatus } from '../api/types'

type BadgeVariant =
  | DocumentStatus
  | 'PROCESSING'
  | 'PROCESSED'
  | 'FAILED'
  | 'MATCH'
  | 'MISMATCH'
  | 'UNCERTAIN'
  | 'AUTO_APPROVE'
  | 'HUMAN_REVIEW'
  | 'AMENDMENT_REQUEST'
  | 'RESULT'
  | 'EMPTY'
  | 'UNSUPPORTED'
  | 'FAILURE'
  | 'ACCEPTED'
  | 'EXTRACTED'
  | 'VALIDATED'
  | 'DECIDED'

const TONE_MAP: Record<string, string> = {
  PROCESSING: 'info',
  ACCEPTED: 'info',
  EXTRACTED: 'info',
  VALIDATED: 'info',
  PROCESSED: 'success',
  DECIDED: 'success',
  MATCH: 'success',
  AUTO_APPROVE: 'success',
  RESULT: 'success',
  FAILED: 'danger',
  MISMATCH: 'danger',
  AMENDMENT_REQUEST: 'danger',
  FAILURE: 'danger',
  UNCERTAIN: 'warning',
  HUMAN_REVIEW: 'warning',
  UNSUPPORTED: 'warning',
  EMPTY: 'neutral',
}

interface StatusBadgeProps {
  status: BadgeVariant | DocumentStatus | string
  showLifecycle?: boolean
}

export function StatusBadge({ status, showLifecycle = false }: StatusBadgeProps) {
  const lifecycle =
    showLifecycle && isDocumentStatus(status)
      ? toLifecycleBadge(status)
      : null

  const displayStatus = lifecycle ?? status
  const tone = TONE_MAP[displayStatus] ?? 'neutral'

  return (
    <span
      role="status"
      aria-label={`Status: ${displayStatus}`}
      className={`status-badge status-badge--${tone}`}
    >
      {displayStatus}
      {lifecycle && lifecycle !== status ? (
        <span className="sr-only"> (document status {status})</span>
      ) : null}
    </span>
  )
}

function isDocumentStatus(value: string): value is DocumentStatus {
  return [
    'ACCEPTED',
    'PROCESSING',
    'EXTRACTED',
    'VALIDATED',
    'DECIDED',
    'FAILED',
  ].includes(value)
}
