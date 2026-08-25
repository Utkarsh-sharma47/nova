interface LoadingStateProps {
  label?: string
}

export function LoadingState({ label = 'Loading…' }: LoadingStateProps) {
  return (
    <section className="panel" role="status" aria-live="polite" aria-busy="true">
      <p>{label}</p>
    </section>
  )
}
