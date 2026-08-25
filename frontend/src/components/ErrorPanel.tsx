interface ErrorPanelProps {
  title?: string
  message: string
  traceId?: string
  code?: string
  retryable?: boolean
  onRetry?: () => void
}

export function ErrorPanel({
  title = 'Error',
  message,
  traceId,
  code,
  retryable,
  onRetry,
}: ErrorPanelProps) {
  return (
    <section
      className="panel panel--danger"
      role="alert"
      aria-live="assertive"
    >
      <h2>{title}</h2>
      <p>{message}</p>
      {code ? (
        <p>
          <strong>Code:</strong> {code}
        </p>
      ) : null}
      {retryable != null ? (
        <p>
          <strong>Retryable:</strong> {retryable ? 'Yes' : 'No'}
        </p>
      ) : null}
      {onRetry ? (
        <div className="button-row">
          <button type="button" className="btn btn--secondary" onClick={onRetry}>
            Try again
          </button>
        </div>
      ) : null}
      {traceId ? (
        <details>
          <summary>Technical details</summary>
          <p>
            <strong>Trace ID:</strong>{' '}
            <code className="mono">{traceId}</code>
          </p>
        </details>
      ) : null}
    </section>
  )
}
