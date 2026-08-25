interface LoadingStateProps {
  label?: string
}

export function LoadingState({ label = 'Loading…' }: LoadingStateProps) {
  return (
    <section
      className="loading-state"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <span className="loading-state__spinner" aria-hidden="true" />
      <p>{label}</p>
    </section>
  )
}
