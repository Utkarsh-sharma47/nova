import { describe, expect, it } from 'vitest'
import { toLifecycleBadge, formatBytes, shortId } from './status'

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

describe('formatBytes', () => {
  it('formats byte sizes', () => {
    expect(formatBytes(512)).toBe('512 B')
    expect(formatBytes(2048)).toBe('2.0 KB')
    expect(formatBytes(2_097_152)).toBe('2.0 MB')
  })
})

describe('shortId', () => {
  it('shortens long ids', () => {
    expect(shortId('11111111-1111-1111-1111-111111111111')).toContain('…')
  })
})
