import type { DocumentStatus, LifecycleBadge } from '../api/types'

const PROCESSING_STATUSES: DocumentStatus[] = [
  'ACCEPTED',
  'PROCESSING',
  'EXTRACTED',
  'VALIDATED',
]

export function toLifecycleBadge(status: DocumentStatus): LifecycleBadge {
  if (status === 'FAILED') {
    return 'FAILED'
  }
  if (status === 'DECIDED') {
    return 'PROCESSED'
  }
  if (PROCESSING_STATUSES.includes(status)) {
    return 'PROCESSING'
  }
  return 'PROCESSING'
}

export function formatTimestamp(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString()
}

export function formatConfidence(value: number | null | undefined): string {
  if (value == null) {
    return '—'
  }
  return `${Math.round(value * 100)}%`
}

export function fieldDisplayName(field: {
  name?: string
  field_name?: string
}): string {
  return field.name ?? field.field_name ?? 'unknown'
}

export function formatFieldValue(value: unknown): string {
  if (value == null) {
    return '—'
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}
