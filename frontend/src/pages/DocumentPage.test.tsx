import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DocumentPage } from './DocumentPage'
import { jsonResponse, mockFetch } from '../test/helpers'

const documentDetail = {
  document_id: 'doc_1',
  shipment_id: 'shp_1',
  customer_id: 'cust_demo',
  document_type: 'INVOICE',
  status: 'DECIDED',
  run_id: 'run_1',
  created_at: '2026-08-25T00:00:00Z',
  updated_at: '2026-08-25T00:05:00Z',
  extraction: {
    status: 'SUCCEEDED',
    fields: [
      {
        name: 'consignee_name',
        value: 'Acme Corp',
        presence: 'KNOWN',
        confidence: 0.92,
        evidence: [{ text: 'Acme Corp', page: 1 }],
      },
    ],
  },
  trace_id: 'trace_doc',
}

const validationResult = {
  validation_id: 'val_1',
  document_id: 'doc_1',
  shipment_id: 'shp_1',
  run_id: 'run_1',
  overall_result: 'UNCERTAIN',
  checks: [
    {
      check_id: 'chk_1',
      rule_id: 'rule_consignee_match',
      field_name: 'consignee_name',
      result: 'UNCERTAIN',
      reason: 'Low confidence on consignee match.',
      expected: { type: 'allow_list_ref' },
      actual: { value: 'Acme Corp', confidence: 0.62 },
    },
  ],
  created_at: '2026-08-25T00:04:00Z',
  trace_id: 'trace_val',
}

const humanReviewDecision = {
  decision_id: 'dec_1',
  document_id: 'doc_1',
  shipment_id: 'shp_1',
  run_id: 'run_1',
  decision: 'HUMAN_REVIEW',
  rationale: 'Validation UNCERTAIN on consignee; confidence below policy.',
  policy_version: 'routing-policy-1',
  inputs: { overall_validation: 'UNCERTAIN' },
  created_at: '2026-08-25T00:04:30Z',
  approval_state: 'NONE',
  trace_id: 'trace_dec',
}

const amendmentDecision = {
  ...humanReviewDecision,
  decision_id: 'dec_2',
  decision: 'AMENDMENT_REQUEST',
  rationale: 'Blocking mismatch requires amendment.',
}

function renderDocument(documentId = 'doc_1') {
  return render(
    <MemoryRouter initialEntries={[`/documents/${documentId}`]}>
      <Routes>
        <Route path="/documents/:documentId" element={<DocumentPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('DocumentPage', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      mockFetch((url) => {
        if (url.includes('/validation')) {
          return jsonResponse(validationResult)
        }
        if (url.includes('/decision')) {
          return jsonResponse(humanReviewDecision)
        }
        if (url.includes('/v1/documents/doc_1')) {
          return jsonResponse(documentDetail)
        }
        return jsonResponse({}, { status: 404 })
      }),
    )
  })

  it('shows loading state while document loads', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise(() => undefined)),
    )

    renderDocument()
    expect(screen.getByText(/loading document/i)).toBeInTheDocument()
  })

  it('renders document metadata and extraction fields', async () => {
    renderDocument()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /document doc_1/i })).toBeInTheDocument()
    })

    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('consignee_name')).toBeInTheDocument()
    expect(screen.getByText('92%')).toBeInTheDocument()
  })

  it('renders validation checks including UNCERTAIN', async () => {
    renderDocument()

    await waitFor(() => {
      expect(screen.getByText(/validation checks/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/low confidence on consignee match/i)).toBeInTheDocument()
    expect(screen.getAllByText('UNCERTAIN').length).toBeGreaterThan(0)
  })

  it('renders HUMAN_REVIEW decision from API', async () => {
    renderDocument()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Routing decision' })).toBeInTheDocument()
    })

    expect(screen.getByText(/validation uncertain on consignee/i)).toBeInTheDocument()
    expect(screen.getAllByText('HUMAN_REVIEW').length).toBeGreaterThan(0)
    expect(screen.queryByText('AUTO_APPROVE')).not.toBeInTheDocument()
  })

  it('renders AMENDMENT_REQUEST decision from API', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch((url) => {
        if (url.includes('/validation')) {
          return jsonResponse({
            ...validationResult,
            overall_result: 'MISMATCH',
            checks: [
              {
                ...validationResult.checks[0],
                result: 'MISMATCH',
              },
            ],
          })
        }
        if (url.includes('/decision')) {
          return jsonResponse(amendmentDecision)
        }
        return jsonResponse(documentDetail)
      }),
    )

    renderDocument()

    await waitFor(() => {
      expect(screen.getAllByText('AMENDMENT_REQUEST').length).toBeGreaterThan(0)
    })
    expect(screen.getByText(/blocking mismatch requires amendment/i)).toBeInTheDocument()
  })

  it('renders failed processing status without inventing a decision', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch((url) => {
        if (url.includes('/validation') || url.includes('/decision')) {
          return jsonResponse(
            {
              error: {
                code: 'NOT_FOUND',
                message: 'Not found',
                trace_id: 'trace_fail',
                retryable: false,
              },
            },
            { status: 404 },
          )
        }
        return jsonResponse({
          ...documentDetail,
          status: 'FAILED',
          extraction: {
            status: 'FAILED',
            fields: [],
          },
        })
      }),
    )

    renderDocument()

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /document doc_1/i })).toBeInTheDocument()
    })

    expect(screen.getAllByText('FAILED').length).toBeGreaterThan(0)
    expect(screen.queryByText('AUTO_APPROVE')).not.toBeInTheDocument()
  })

  it('does not execute unsafe HTML from API responses', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch((url) => {
        if (url.includes('/validation')) {
          return jsonResponse(validationResult)
        }
        if (url.includes('/decision')) {
          return jsonResponse(humanReviewDecision)
        }
        return jsonResponse({
          ...documentDetail,
          extraction: {
            status: 'SUCCEEDED',
            fields: [
              {
                name: 'notes',
                value: '<img src=x onerror="window.__xss=1">',
                presence: 'KNOWN',
                confidence: 0.5,
                evidence: [{ text: '<script>alert(1)</script>' }],
              },
            ],
          },
        })
      }),
    )

    renderDocument()

    await waitFor(() => {
      expect(screen.getByText(/<img src=x onerror/)).toBeInTheDocument()
    })

    expect((window as Window & { __xss?: number }).__xss).toBeUndefined()
    expect(document.body.innerHTML).not.toMatch(/<script>alert\(1\)<\/script>/)
    expect(screen.getByText(/<script>alert\(1\)<\/script>/)).toBeInTheDocument()
  })
})
