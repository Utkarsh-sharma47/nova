interface EmptyStateProps {
  title?: string
  message: string
}

export function EmptyState({ title = 'No data', message }: EmptyStateProps) {
  return (
    <section className="panel" role="status">
      <h2>{title}</h2>
      <p>{message}</p>
    </section>
  )
}
