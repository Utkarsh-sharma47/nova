import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DashboardPage } from './DashboardPage'
import { errorResponse, jsonResponse, mockFetch } from '../test/helpers'

const CUSTOMER = '11111111-1111-1111-1111-111111111111'

describe('DashboardPage', () => {
  beforeEach(() => {
    sessionStorage.clear()
    vi.stubGlobal(
      'fetch',
      mockFetch((url) => {
        if (url.includes('/v1/ops/summary')) {
          return jsonResponse({
            customer_id: CUSTOMER,
            totals: {
              documents: 3,
              processing: 1,
              decided: 2,
              failed: 0,
              human_review: 1,
              amendment_request: 0,
              auto_approve: 1,
            },
            validation_outcomes: {
              MATCH: 1,
              MISMATCH: 1,
              UNCERTAIN: 1,
            },
            recent_documents: [
              {
                document_id: 'doc_recent',
                shipment_id: 'shp_1',
                customer_id: CUSTOMER,
                document_type: 'INVOICE',
                status: 'DECIDED',
                run_id: 'run_1',
                created_at: '2026-08-25T00:00:00Z',
                updated_at: '2026-08-25T00:05:00Z',
              },
            ],
            recent_decisions: [
              {
                decision_id: 'dec_1',
                document_id: 'doc_recent',
                shipment_id: 'shp_1',
                decision: 'HUMAN_REVIEW',
                created_at: '2026-08-25T00:05:00Z',
              },
            ],
            trace_id: 'trace_dash',
          })
        }
        return jsonResponse({}, { status: 404 })
      }),
    )
  })

  it('shows empty guidance without customer id', () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )
    expect(
      screen.getByText(/provide a customer uuid or create a demo customer/i),
    ).toBeInTheDocument()
  })

  it('renders dashboard totals from API', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await user.type(
      screen.getByLabelText(/customer id/i),
      CUSTOMER,
    )
    await user.click(screen.getByRole('button', { name: /load dashboard/i }))

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getAllByText('doc_recent').length).toBeGreaterThan(0)
      expect(screen.getByLabelText(/validation outcomes/i)).toBeInTheDocument()
      expect(screen.getAllByText('shp_1').length).toBeGreaterThan(0)
      expect(screen.getAllByRole('columnheader', { name: /shipment/i }).length).toBeGreaterThan(0)
      expect(screen.getAllByRole('columnheader', { name: /decision/i }).length).toBeGreaterThan(0)
    })
  })

  it('rejects invalid customer UUID before calling the API', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/customer id/i), 'not-a-uuid')
    await user.click(screen.getByRole('button', { name: /load dashboard/i }))

    expect(screen.getByText(/valid customer uuid/i)).toBeInTheDocument()
    expect(fetch).not.toHaveBeenCalled()
  })

  it('offers retry after API failure', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch(() =>
        errorResponse(503, {
          code: 'DEPENDENCY_UNAVAILABLE',
          message: 'Database unavailable',
          retryable: true,
          trace_id: 'trace_fail',
        }),
      ),
    )

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/customer id/i), CUSTOMER)
    await user.click(screen.getByRole('button', { name: /load dashboard/i }))

    await waitFor(() => {
      expect(screen.getByText(/database unavailable/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    })
  })

  it('shows API failure', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch(() =>
        errorResponse(503, {
          code: 'DEPENDENCY_UNAVAILABLE',
          message: 'Database unavailable',
          retryable: true,
          trace_id: 'trace_fail',
        }),
      ),
    )

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/customer id/i), CUSTOMER)
    await user.click(screen.getByRole('button', { name: /load dashboard/i }))

    await waitFor(() => {
      expect(screen.getByText(/database unavailable/i)).toBeInTheDocument()
      expect(screen.getByText(/trace_fail/)).toBeInTheDocument()
    })
  })
})
