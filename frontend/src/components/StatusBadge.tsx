import { toLifecycleBadge } from '../utils/status'
import type { AgreementCategory, DocumentStatus } from '../api/types'

type BadgeVariant =
  | DocumentStatus
  | AgreementCategory
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
  | 'STRONG AGREEMENT'
  | 'PARTIAL AGREEMENT'
  | 'WEAK AGREEMENT'

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
  STRONG_AGREEMENT: 'success',
  'STRONG AGREEMENT': 'success',
  FAILED: 'danger',
  MISMATCH: 'danger',
  AMENDMENT_REQUEST: 'danger',
  FAILURE: 'danger',
  WEAK_AGREEMENT: 'danger',
  'WEAK AGREEMENT': 'danger',
  UNCERTAIN: 'warning',
  HUMAN_REVIEW: 'warning',
  UNSUPPORTED: 'warning',
  PARTIAL_AGREEMENT: 'warning',
  'PARTIAL AGREEMENT': 'warning',
  EMPTY: 'neutral',
}

const AGREEMENT_LABELS: Record<string, string> = {
  STRONG_AGREEMENT: 'STRONG AGREEMENT',
  PARTIAL_AGREEMENT: 'PARTIAL AGREEMENT',
  WEAK_AGREEMENT: 'WEAK AGREEMENT',
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

  const displayStatus = lifecycle ?? AGREEMENT_LABELS[status] ?? status
  const tone = TONE_MAP[String(displayStatus)] ?? TONE_MAP[String(status)] ?? 'neutral'

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
