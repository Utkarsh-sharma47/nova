import { describe, expect, it } from 'vitest'
import { toLifecycleBadge } from './status'

describe('toLifecycleBadge', () => {
  it('maps in-progress document statuses to PROCESSING', () => {
    expect(toLifecycleBadge('ACCEPTED')).toBe('PROCESSING')
    expect(toLifecycleBadge('PROCESSING')).toBe('PROCESSING')
    expect(toLifecycleBadge('EXTRACTED')).toBe('PROCESSING')
    expect(toLifecycleBadge('VALIDATED')).toBe('PROCESSING')
  })

  it('maps DECIDED to PROCESSED', () => {
    expect(toLifecycleBadge('DECIDED')).toBe('PROCESSED')
  })

  it('maps FAILED to FAILED', () => {
    expect(toLifecycleBadge('FAILED')).toBe('FAILED')
  })
})
