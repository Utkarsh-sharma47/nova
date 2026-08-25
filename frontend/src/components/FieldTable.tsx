import type { ExtractedField } from '../api/types'
import {
  fieldDisplayName,
  formatConfidence,
  formatFieldValue,
} from '../utils/status'
import { EvidenceList } from './EvidenceList'

interface FieldTableProps {
  fields: ExtractedField[]
}

export function FieldTable({ fields }: FieldTableProps) {
  if (!fields.length) {
    return <p className="form-hint">No extracted fields available.</p>
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th scope="col">Field</th>
          <th scope="col">Value</th>
          <th scope="col">Presence</th>
          <th scope="col">Confidence</th>
          <th scope="col">Uncertainty</th>
          <th scope="col">Evidence</th>
        </tr>
      </thead>
      <tbody>
        {fields.map((field) => (
          <tr key={fieldDisplayName(field)}>
            <td>{fieldDisplayName(field)}</td>
            <td>{formatFieldValue(field.value)}</td>
            <td>{field.presence}</td>
            <td>{formatConfidence(field.confidence)}</td>
            <td>{field.uncertainty ?? '—'}</td>
            <td>
              <EvidenceList evidence={field.evidence ?? []} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
