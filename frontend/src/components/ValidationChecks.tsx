import type { ValidationCheck } from '../api/types'
import { formatFieldValue } from '../utils/status'
import { StatusBadge } from './StatusBadge'

interface ValidationChecksProps {
  checks: ValidationCheck[]
  overallResult?: string
}

export function ValidationChecks({ checks, overallResult }: ValidationChecksProps) {
  if (!checks.length) {
    return <p className="form-hint">No validation checks available.</p>
  }

  return (
    <section aria-labelledby="validation-heading">
      <h2 id="validation-heading">Validation checks</h2>
      {overallResult ? (
        <p>
          Overall: <StatusBadge status={overallResult as 'MATCH' | 'MISMATCH' | 'UNCERTAIN'} />
        </p>
      ) : null}
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Rule</th>
            <th scope="col">Field</th>
            <th scope="col">Result</th>
            <th scope="col">Reason</th>
            <th scope="col">Expected</th>
            <th scope="col">Actual</th>
          </tr>
        </thead>
        <tbody>
          {checks.map((check) => (
            <tr
              key={check.check_id}
              className={check.result === 'UNCERTAIN' ? 'panel--highlight' : undefined}
            >
              <td>{check.rule_id}</td>
              <td>{check.field_name ?? '—'}</td>
              <td>
                <StatusBadge status={check.result} />
              </td>
              <td>{check.reason}</td>
              <td>{formatFieldValue(check.expected)}</td>
              <td>{formatFieldValue(check.actual)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
