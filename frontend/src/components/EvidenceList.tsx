import type { Evidence } from '../api/types'

interface EvidenceListProps {
  evidence: Evidence[]
}

export function EvidenceList({ evidence }: EvidenceListProps) {
  if (!evidence.length) {
    return <p className="form-hint">No evidence recorded.</p>
  }

  return (
    <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
      {evidence.map((item, index) => (
        <li key={item.evidence_id ?? `ev-${index}`}>
          {item.text ?? '(no text)'}
          {item.page != null ? ` — page ${item.page}` : ''}
          {item.source ? ` — ${item.source}` : ''}
        </li>
      ))}
    </ul>
  )
}
