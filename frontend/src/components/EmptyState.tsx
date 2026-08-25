import type { ReactNode } from 'react'

interface EmptyStateProps {
  title?: string
  message: string
  action?: ReactNode
}

export function EmptyState({
  title = 'No data',
  message,
  action,
}: EmptyStateProps) {
  return (
    <section className="empty-state" role="status">
      <div className="empty-state__icon" aria-hidden="true">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <rect
            x="6"
            y="8"
            width="28"
            height="24"
            rx="2"
            stroke="currentColor"
            strokeWidth="1.5"
          />
          <path
            d="M12 16h16M12 21h10M12 26h8"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <h2 className="empty-state__title">{title}</h2>
      <p className="empty-state__message">{message}</p>
      {action ? <div className="empty-state__action">{action}</div> : null}
    </section>
  )
}
