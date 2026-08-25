import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QueryPage } from './QueryPage'
import { errorResponse, jsonResponse, mockFetch } from '../test/helpers'

const CUSTOMER = '11111111-1111-1111-1111-111111111111'

describe('QueryPage', () => {
  beforeEach(() => {
    sessionStorage.setItem('nova.customer_id', CUSTOMER)
    vi.stubGlobal('fetch', mockFetch(() => jsonResponse({ status: 'ok' })))
  })

  it('shows loading state while querying', async () => {
    const user = userEvent.setup()
    let resolveQuery!: (value: Response) => void
    const queryPromise = new Promise<Response>((resolve) => {
      resolveQuery = resolve
    })

    vi.stubGlobal('fetch', vi.fn(() => queryPromise))

    render(
      <MemoryRouter>
        <QueryPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/question/i), 'Which shipments need review?')
    await user.click(screen.getByRole('button', { name: /submit query/i }))

    expect(screen.getByText(/running query/i)).toBeInTheDocument()

    resolveQuery(
      jsonResponse({
        question: 'Which shipments need review?',
        status: 'RESULT',
        result: {
          answer_summary: '1 shipment is in HUMAN_REVIEW.',
          records: [],
          citations: [],
        },
        trace_id: 'trace_q',
      }),
    )

    await waitFor(() => {
      expect(screen.getByText(/1 shipment is in human_review/i)).toBeInTheDocument()
    })
  })

  it('renders RESULT status', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch((url, init) => {
        expect(url).toContain('/v1/query')
        expect(init?.method).toBe('POST')
        return jsonResponse({
          question: 'List human review shipments',
          interpreted_intent: {
            name: 'list_shipments_by_decision',
            version: '1',
            parameters: { decision: 'HUMAN_REVIEW' },
          },
          status: 'RESULT',
          result: {
            answer_summary: '2 shipments are in HUMAN_REVIEW.',
            records: [
              {
                type: 'shipment',
                shipment_id: 'shp_1',
                decision: 'HUMAN_REVIEW',
              },
            ],
            citations: [],
          },
          trace_id: 'trace_result',
        })
      }),
    )

    render(
      <MemoryRouter>
        <QueryPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/question/i), 'List human review shipments')
    await user.click(screen.getByRole('button', { name: /submit query/i }))

    await waitFor(() => {
      expect(screen.getByText(/2 shipments are in human_review/i)).toBeInTheDocument()
      expect(screen.getByText('RESULT')).toBeInTheDocument()
    })
  })

  it('renders grounded agreement count and list answers', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch(() =>
        jsonResponse({
          question: 'How many strong agreement documents are there?',
          interpreted_intent: {
            name: 'count_documents_by_agreement',
            version: '1',
            parameters: { agreement: 'STRONG_AGREEMENT' },
            confidence: 0.92,
          },
          status: 'RESULT',
          result: {
            answer_summary: '2 documents have STRONG_AGREEMENT.',
            records: [
              {
                type: 'agreement_count',
                agreement: 'STRONG_AGREEMENT',
                count: 2,
              },
            ],
            citations: [],
          },
          trace_id: 'trace_agreement',
        }),
      ),
    )

    render(
      <MemoryRouter>
        <QueryPage />
      </MemoryRouter>,
    )

    await user.type(
      screen.getByLabelText(/question/i),
      'How many strong agreement documents are there?',
    )
    await user.click(screen.getByRole('button', { name: /submit query/i }))

    await waitFor(() => {
      expect(screen.getByText('RESULT')).toBeInTheDocument()
      expect(screen.getByText(/2 documents have STRONG_AGREEMENT/)).toBeInTheDocument()
      expect(screen.getByText('STRONG AGREEMENT')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
    })
  })

  it('renders EMPTY status', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch(() =>
        jsonResponse({
          question: 'Any failed docs?',
          status: 'EMPTY',
          result: {
            answer_summary: 'No matching records found.',
            records: [],
            citations: [],
          },
          trace_id: 'trace_empty',
        }),
      ),
    )

    render(
      <MemoryRouter>
        <QueryPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/question/i), 'Any failed docs?')
    await user.click(screen.getByRole('button', { name: /submit query/i }))

    await waitFor(() => {
      expect(screen.getByText(/no matching records found/i)).toBeInTheDocument()
      expect(screen.getByText('EMPTY')).toBeInTheDocument()
    })
  })

  it('renders UNSUPPORTED status', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch(() =>
        jsonResponse({
          question: 'Predict vessel ETA',
          status: 'UNSUPPORTED',
          unsupported: {
            reason_code: 'INTENT_NOT_SUPPORTED',
            message: 'Nova cannot answer questions that require predicting future vessel ETAs.',
            suggestions: ['Ask which shipments are in HUMAN_REVIEW'],
          },
          trace_id: 'trace_unsupported',
        }),
      ),
    )

    render(
      <MemoryRouter>
        <QueryPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/question/i), 'Predict vessel ETA')
    await user.click(screen.getByRole('button', { name: /submit query/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/cannot answer questions that require predicting/i),
      ).toBeInTheDocument()
      expect(screen.getByText('UNSUPPORTED')).toBeInTheDocument()
    })
  })

  it('renders FAILURE status', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch(() =>
        jsonResponse({
          question: 'Summarize run',
          status: 'FAILURE',
          failure: {
            code: 'AI_PROVIDER_ERROR',
            message: 'Query interpretation temporarily unavailable.',
            retryable: true,
          },
          trace_id: 'trace_failure',
        }),
      ),
    )

    render(
      <MemoryRouter>
        <QueryPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/question/i), 'Summarize run')
    await user.click(screen.getByRole('button', { name: /submit query/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/query interpretation temporarily unavailable/i),
      ).toBeInTheDocument()
      expect(screen.getByText('FAILURE')).toBeInTheDocument()
    })
  })

  it('shows API failure for transport errors', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch(() =>
        errorResponse(502, {
          code: 'UPSTREAM_ERROR',
          message: 'Upstream dependency failed.',
          retryable: true,
          trace_id: 'trace_502',
        }),
      ),
    )

    render(
      <MemoryRouter>
        <QueryPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/question/i), 'Get document')
    await user.click(screen.getByRole('button', { name: /submit query/i }))

    await waitFor(() => {
      expect(screen.getByText(/upstream dependency failed/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    })
  })

  it('rejects invalid customer UUID client-side', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <QueryPage />
      </MemoryRouter>,
    )

    await user.clear(screen.getByLabelText(/customer id/i))
    await user.type(screen.getByLabelText(/customer id/i), 'bad-id')
    await user.type(screen.getByLabelText(/question/i), 'How many shipments are in human review?')
    await user.click(screen.getByRole('button', { name: /submit query/i }))

    expect(screen.getByText(/customer id must be a valid uuid/i)).toBeInTheDocument()
    expect(fetch).not.toHaveBeenCalled()
  })
})
