import type { CSSProperties } from 'react'
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

const VARIANT_STYLES: Record<string, CSSProperties> = {
  PROCESSING: { background: '#ebf4ff', color: '#2b6cb0', borderColor: '#90cdf4' },
  PROCESSED: { background: '#f0fff4', color: '#276749', borderColor: '#9ae6b4' },
  FAILED: { background: '#fff5f5', color: '#9b2c2c', borderColor: '#feb2b2' },
  MATCH: { background: '#f0fff4', color: '#276749', borderColor: '#9ae6b4' },
  MISMATCH: { background: '#fff5f5', color: '#9b2c2c', borderColor: '#feb2b2' },
  UNCERTAIN: { background: '#fffaf0', color: '#975a16', borderColor: '#fbd38d' },
  AUTO_APPROVE: { background: '#f0fff4', color: '#276749', borderColor: '#9ae6b4' },
  HUMAN_REVIEW: { background: '#fffaf0', color: '#975a16', borderColor: '#fbd38d' },
  AMENDMENT_REQUEST: { background: '#fff5f5', color: '#9b2c2c', borderColor: '#feb2b2' },
  RESULT: { background: '#f0fff4', color: '#276749', borderColor: '#9ae6b4' },
  EMPTY: { background: '#edf2f7', color: '#4a5568', borderColor: '#cbd5e0' },
  UNSUPPORTED: { background: '#fffaf0', color: '#975a16', borderColor: '#fbd38d' },
  FAILURE: { background: '#fff5f5', color: '#9b2c2c', borderColor: '#feb2b2' },
}

interface StatusBadgeProps {
  status: BadgeVariant | DocumentStatus
  showLifecycle?: boolean
}

export function StatusBadge({ status, showLifecycle = false }: StatusBadgeProps) {
  const lifecycle =
    showLifecycle && isDocumentStatus(status)
      ? toLifecycleBadge(status)
      : null

  const displayStatus = lifecycle ?? status
  const style = VARIANT_STYLES[displayStatus] ?? {
    background: '#edf2f7',
    color: '#4a5568',
    borderColor: '#cbd5e0',
  }

  return (
    <span
      role="status"
      aria-label={`Status: ${displayStatus}`}
      style={{
        display: 'inline-block',
        padding: '0.125rem 0.5rem',
        border: '1px solid',
        borderRadius: '2px',
        fontSize: '0.75rem',
        fontWeight: 600,
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
        ...style,
      }}
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
