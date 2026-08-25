interface ErrorPanelProps {
  title?: string
  message: string
  traceId?: string
  code?: string
  retryable?: boolean
}

export function ErrorPanel({
  title = 'Error',
  message,
  traceId,
  code,
  retryable,
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
      {traceId ? (
        <details>
          <summary>Technical details</summary>
          <p>
            <strong>Trace ID:</strong>{' '}
            <code style={{ fontFamily: 'var(--font-mono)' }}>{traceId}</code>
          </p>
        </details>
      ) : null}
    </section>
  )
}
