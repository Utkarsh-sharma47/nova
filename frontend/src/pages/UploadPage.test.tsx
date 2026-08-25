import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { UploadPage } from './UploadPage'
import { errorResponse, jsonResponse, mockFetch } from '../test/helpers'

const CUSTOMER = '11111111-1111-1111-1111-111111111111'

describe('UploadPage', () => {
  beforeEach(() => {
    sessionStorage.setItem('nova.customer_id', CUSTOMER)
    vi.stubGlobal('fetch', mockFetch(() => jsonResponse({ status: 'ok' })))
  })

  it('shows loading state while uploading', async () => {
    const user = userEvent.setup()
    let resolveUpload!: (value: Response) => void
    const uploadPromise = new Promise<Response>((resolve) => {
      resolveUpload = resolve
    })

    vi.stubGlobal(
      'fetch',
      vi.fn(() => uploadPromise),
    )

    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    )

    const fileInput = screen.getByLabelText(/file/i)
    const file = new File(['invoice'], 'invoice.pdf', { type: 'application/pdf' })
    await user.upload(fileInput, file)
    await user.click(screen.getByRole('button', { name: /upload document/i }))

    expect(screen.getByText(/upload in progress/i)).toBeInTheDocument()

    resolveUpload(
      jsonResponse(
        {
          document_id: 'doc_1',
          shipment_id: 'shp_1',
          run_id: 'run_1',
          status: 'ACCEPTED',
          idempotent_replay: false,
          trace_id: 'trace_1',
        },
        { status: 202 },
      ),
    )

    await waitFor(() => {
      expect(screen.getByText(/upload received/i)).toBeInTheDocument()
      expect(
        screen.getByText(/upload acceptance is not a routing decision/i),
      ).toBeInTheDocument()
    })
  })

  it('handles upload success', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch((url, init) => {
        expect(url).toContain('/v1/documents')
        expect(init?.method).toBe('POST')
        return jsonResponse(
          {
            document_id: 'doc_success',
            shipment_id: 'shp_success',
            run_id: 'run_success',
            status: 'ACCEPTED',
            idempotent_replay: false,
            trace_id: 'trace_success',
          },
          { status: 202 },
        )
      }),
    )

    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    )

    const file = new File(['data'], 'doc.pdf', { type: 'application/pdf' })
    await user.upload(screen.getByLabelText(/file/i), file)
    await user.click(screen.getByRole('button', { name: /upload document/i }))

    await waitFor(() => {
      expect(screen.getByText('doc_success')).toBeInTheDocument()
      expect(screen.getByText('shp_success')).toBeInTheDocument()
    })
  })

  it('shows client validation error for unsupported file type', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    )

    const file = new File(['data'], 'doc.exe', {
      type: 'application/octet-stream',
    })
    const fileInput = screen.getByLabelText(/file/i)
    fireEvent.change(fileInput, { target: { files: [file] } })
    await user.click(screen.getByRole('button', { name: /upload document/i }))

    expect(screen.getByText(/only pdf, plain text, png, and jpeg/i)).toBeInTheDocument()
    expect(fetch).not.toHaveBeenCalled()
  })

  it('shows API validation error (422)', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch(() =>
        errorResponse(422, {
          code: 'VALIDATION_FAILED',
          message: 'Unsupported document type.',
          retryable: false,
          trace_id: 'trace_422',
        }),
      ),
    )

    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    )

    const file = new File(['data'], 'doc.pdf', { type: 'application/pdf' })
    await user.upload(screen.getByLabelText(/file/i), file)
    await user.click(screen.getByRole('button', { name: /upload document/i }))

    await waitFor(() => {
      expect(screen.getByText(/unsupported document type/i)).toBeInTheDocument()
      expect(screen.getByText(/VALIDATION_FAILED/)).toBeInTheDocument()
    })
  })

  it('shows idempotency conflict (409)', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      mockFetch(() =>
        errorResponse(409, {
          code: 'IDEMPOTENCY_KEY_REUSE_MISMATCH',
          message: 'Idempotency key reused with different payload.',
          retryable: false,
          trace_id: 'trace_409',
        }),
      ),
    )

    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    )

    const file = new File(['data'], 'doc.pdf', { type: 'application/pdf' })
    await user.upload(screen.getByLabelText(/file/i), file)
    await user.click(screen.getByRole('button', { name: /upload document/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/idempotency key reused with different payload/i),
      ).toBeInTheDocument()
    })
  })

  it('shows network failure', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))),
    )

    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    )

    const file = new File(['data'], 'doc.pdf', { type: 'application/pdf' })
    await user.upload(screen.getByLabelText(/file/i), file)
    await user.click(screen.getByRole('button', { name: /upload document/i }))

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    })
  })
})
